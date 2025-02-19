from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.files.storage import default_storage
from django.db.models import Count, F
from django.utils import timezone
import hashlib
import json
import fitz
import os
from datetime import datetime
from .models import File, Annotation, AnnotationHistory
from .serializers import FileSerializer, AnnotationSerializer, AnnotationHistorySerializer
from .validators import validate_cv_json

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'token': str(refresh.access_token),
                'refresh': str(refresh),
                'username': user.username,
                'user_id': user.id
            })
        return Response(
            {'error': '用户名或密码错误'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 只返回未删除的文件
        return super().get_queryset().filter(is_deleted=False)

    def perform_create(self, serializer):
        pdf_file = self.request.FILES['pdf_file']
        json_file = self.request.FILES['json_file']
        
        try:
            # 处理PDF文件
            pdf_file.seek(0)
            pdf_content = pdf_file.read()
            checksum = hashlib.sha256(pdf_content).hexdigest()
            
            # 获取PDF元数据
            pdf_doc = fitz.open(stream=pdf_content, filetype="pdf")
            page_count = len(pdf_doc)
            file_size = len(pdf_content)
            
            # 验证并读取JSON
            json_file.seek(0)
            json_content = json.load(json_file)
            
            # 重置文件指针
            pdf_file.seek(0)
            json_file.seek(0)
            
            # 保存文件
            file_instance = serializer.save(
                uploaded_by=self.request.user,
                status='ready',
                checksum=checksum,
                page_count=page_count,
                file_size=file_size,
                metadata={'json_structure': list(json_content.keys())}
            )
            
            # 创建一个初始标注，包含整个 JSON
            annotation = Annotation.objects.create(
                file=file_instance,
                field_type='root',  # 根节点
                field_path='root',  # 根路径
                pdf_content='',  # 初始为空
                json_content=json_content,  # 保存整个 JSON
                position={},  # 初始为空
                verification_status='pending',
                is_correct=False,
                confidence_score=0.0,
                annotator=self.request.user,
                version=1
            )
            
            # 创建初始历史记录
            AnnotationHistory.objects.create(
                annotation=annotation,
                field_path='root',
                old_value=None,
                new_value=json_content,  # 保存完整的 JSON
                pdf_content='',
                position={},
                verification_status='pending',
                change_type='create',
                change_description='创建初始JSON',
                modified_by=self.request.user,
                version=1
            )
            
            return file_instance
            
        except Exception as e:
            raise serializers.ValidationError(f'文件处理失败: {str(e)}')

    def _get_field_type(self, field_path):
        """根据字段路径判断字段类型"""
        if field_path.startswith('personal_info'):
            return 'personal_info'
        elif field_path.startswith('education'):
            return 'education'
        elif field_path.startswith('work_experience'):
            return 'work_experience'
        elif field_path.startswith('skills'):
            return 'skills'
        elif field_path.startswith('projects'):
            return 'projects'
        elif field_path.startswith('certificates'):
            return 'certificates'
        elif field_path.startswith('languages'):
            return 'languages'
        else:
            return 'others'

    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        file = self.get_object()
        page = request.query_params.get('page', 1)
        try:
            page = int(page)
            pdf_doc = fitz.open(file.pdf_file.path)
            if 1 <= page <= len(pdf_doc):
                page_obj = pdf_doc[page-1]
                pix = page_obj.get_pixmap()
                preview_dir = os.path.join(settings.MEDIA_ROOT, 'previews')
                os.makedirs(preview_dir, exist_ok=True)
                preview_path = os.path.join('previews', f'{file.id}_page_{page}.png')
                pix.save(os.path.join(settings.MEDIA_ROOT, preview_path))
                return Response({
                    'preview_url': request.build_absolute_uri(settings.MEDIA_URL + preview_path),
                    'page': page,
                    'total_pages': len(pdf_doc)
                })
            return Response(
                {'error': 'Invalid page number'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        file = self.get_object()
        try:
            # 获取最新版本的标注
            annotation = file.annotations.filter(is_deleted=False).order_by('-version').first()
            if not annotation:
                return Response(
                    {'error': '找不到标注'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            json_content = annotation.json_content
            total_fields = count_total_fields(json_content)
            verified_fields = count_verified_fields(json_content)  # 计算带有 -comlhj 后缀的字段数
            progress = (verified_fields / total_fields * 100) if total_fields > 0 else 0
            
            # 更新文件的 metadata
            file.metadata = {
                **file.metadata,
                'total_fields': total_fields,
                'verified_fields': verified_fields,
                'progress': round(progress, 2)
            }
            file.save()
            
            return Response({
                'total_fields': total_fields,
                'verified_fields': verified_fields,
                'progress': round(progress, 2)
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        file = self.get_object()
        annotations = file.annotations.all()
        history = AnnotationHistory.objects.filter(
            annotation__in=annotations
        ).order_by('-modified_at')
        serializer = AnnotationHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def pdf_info(self, request, pk=None):
        file = self.get_object()
        try:
            pdf_doc = fitz.open(file.pdf_file.path)
            return Response({
                'pdf_url': request.build_absolute_uri(file.pdf_file.url),
                'total_pages': len(pdf_doc),
                'file_name': file.name,
                'file_size': file.file_size,
                'uploaded_at': file.uploaded_at
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_destroy(self, instance):
        try:
            # 删除本地文件
            if instance.pdf_file and os.path.isfile(instance.pdf_file.path):
                os.remove(instance.pdf_file.path)
            if instance.json_file and os.path.isfile(instance.json_file.path):
                os.remove(instance.json_file.path)
            
            # 软删除文件和相关标注
            instance.soft_delete(self.request.user)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {'error': f'删除失败: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

class AnnotationViewSet(viewsets.ModelViewSet):
    queryset = Annotation.objects.all()
    serializer_class = AnnotationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 只返回未删除的标注
        queryset = super().get_queryset().filter(is_deleted=False)
        file_id = self.request.query_params.get('file_id')
        if file_id:
            # 返回文件的最新版本标注
            return queryset.filter(file_id=file_id).order_by('-version')[:1]
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        # 创建标注
        annotation = serializer.save(
            annotator=self.request.user,
            version=1,
            position={}  # 添加默认的空字典作为 position
        )
        
        # 创建初始历史记录
        AnnotationHistory.objects.create(
            annotation=annotation,
            field_path=annotation.field_path,
            old_value=None,
            new_value=annotation.json_content,
            pdf_content=annotation.pdf_content,
            position={},  # 这里也添加默认值
            verification_status=annotation.verification_status,
            change_type='create',
            change_description='创建初始标注',
            modified_by=self.request.user,
            version=1
        )

    def perform_update(self, serializer):
        annotation = serializer.instance
        old_content = annotation.json_content
        new_content = serializer.validated_data.get('json_content', old_content)
        
        # 创建新的历史记录
        AnnotationHistory.objects.create(
            annotation=annotation,
            field_path='root',
            old_value=old_content,
            new_value=new_content,
            pdf_content=annotation.pdf_content,
            position=annotation.position,
            verification_status=serializer.validated_data.get('verification_status', annotation.verification_status),
            change_type='update',
            change_description=f'更新 JSON 版本 {annotation.version + 1}',
            modified_by=self.request.user,
            version=annotation.version + 1
        )
        
        # 更新标注
        annotation = serializer.save(
            version=annotation.version + 1,
            updated_at=timezone.now()
        )

    @action(detail=False, methods=['post'])
    def batch_verify(self, request):
        """批量验证字段"""
        file_id = request.data.get('file_id')
        annotations = request.data.get('annotations', [])
        
        results = []
        for anno in annotations:
            field_path = anno['field_path']
            pdf_content = anno['pdf_content']
            json_content = anno['json_content']
            position = anno['position']
            
            # 创建或更新标注
            annotation = Annotation.objects.create(
                file_id=file_id,
                field_type=get_field_type(field_path),
                field_path=field_path,
                pdf_content=pdf_content,
                json_content=json_content,
                position=position,
                verification_status='verified' if anno['is_correct'] else 'incorrect',
                is_correct=anno['is_correct'],
                confidence_score=anno['confidence_score'],
                comment=anno['comment'],
                annotator=request.user
            )
            
            results.append(annotation)
        
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_missing_field(self, request, pk=None):
        """添加PDF中发现但JSON中缺失的字段"""
        annotation = self.get_object()
        field_path = request.data.get('field_path')
        pdf_content = request.data.get('pdf_content')
        position = request.data.get('position')
        
        annotation.verification_status = 'missing'
        annotation.pdf_content = pdf_content
        annotation.position = position
        annotation.comment = f"JSON中缺失字段: {field_path}"
        annotation.save()
        
        return Response(self.get_serializer(annotation).data)

    @action(detail=True, methods=['POST'])
    def rollback(self, request, pk=None):
        """回滚到指定版本"""
        try:
            # 获取标注对象
            try:
                annotation = Annotation.objects.get(file_id=pk)
            except Annotation.DoesNotExist:
                return Response(
                    {'error': f'找不到 ID 为 {pk} 的标注记录'},
                    status=status.HTTP_404_NOT_FOUND
                )

            version = request.data.get('version')
            historyId = request.data.get('historyId')
            if not version:
                return Response(
                    {'error': '必须提供目标版本号'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            print(f"Debug: annotation_id={pk}, version={version}")
            
            # 获取指定版本的历史记录
            history = AnnotationHistory.objects.filter(
                annotation_id=annotation.id,
                version=version
            ).first()
            
            if not history:
                return Response(
                    {'error': f'标注 {annotation.id} 的版本 {version} 不存在'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            print(f"Debug: found history record: {history.id}")
            
            # 保存当前版本到历史记录
            AnnotationHistory.objects.create(
                annotation=annotation,
                field_path='root',
                old_value=annotation.json_content,
                new_value=history.new_value,
                pdf_content=annotation.pdf_content,
                position=annotation.position,
                verification_status=annotation.verification_status,
                change_type='rollback',
                change_description=f'回滚到版本 {version}',
                modified_by=request.user,
                version=annotation.version + 1
            )
            
            # 更新标注为历史版本的内容
            annotation.json_content = history.new_value
            annotation.version += 1
            annotation.save()
            
            return Response(self.get_serializer(annotation).data)
            
        except Exception as e:
            print(f"Error in rollback: {str(e)}")
            return Response(
                {'error': f'回滚失败: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['POST'])
    def verify_field(self, request, pk=None):
        """更新特定字段的验证状态"""
        annotation = self.get_object()
        field_path = request.data.get('field_path')  # 例如: "personal_info.name.first_name"
        verified = request.data.get('verified', True)
        
        if not field_path:
            return Response(
                {'error': '必须提供 field_path'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # 更新字段验证状态
        json_content = annotation.json_content
        path_parts = field_path.split('.')
        
        # 递归更新指定字段的验证状态
        def update_field(data, parts):
            if len(parts) == 1:
                if isinstance(data.get(parts[0]), dict) and 'value' in data[parts[0]]:
                    data[parts[0]]['verified'] = verified
                return True
            if parts[0] in data:
                return update_field(data[parts[0]], parts[1:])
            return False
            
        if update_field(json_content, path_parts):
            # 创建新的历史记录
            AnnotationHistory.objects.create(
                annotation=annotation,
                field_path=field_path,
                old_value=None,
                new_value={'verified': verified},
                pdf_content=annotation.pdf_content,
                position=annotation.position,
                verification_status='verified' if verified else 'pending',
                change_type='verify',
                change_description=f'{"验证" if verified else "取消验证"}字段 {field_path}',
                modified_by=request.user,
                version=annotation.version + 1
            )
            
            # 更新标注
            annotation.json_content = json_content
            annotation.version += 1
            annotation.save()
            
            return Response(self.get_serializer(annotation).data)
        
        return Response(
            {'error': f'字段 {field_path} 不存在'},
            status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=True, methods=['PUT'])
    def verify(self, request, pk=None):
        """更新当前版本的 JSON（字段验证状态）"""
        annotation = self.get_object()
        new_json = request.data.get('json_content')
        
        if not new_json:
            return Response(
                {'error': '必须提供 json_content'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 直接更新当前版本的标注
            annotation.json_content = new_json
            annotation.save()
            
            # 计算新的进度
            total_fields = count_total_fields(new_json)
            verified_fields = count_verified_fields(new_json)
            progress = (verified_fields / total_fields * 100) if total_fields > 0 else 0
            
            # 更新文件进度
            file = annotation.file
            file.metadata = {
                **file.metadata,
                'total_fields': total_fields,
                'verified_fields': verified_fields,
                'progress': round(progress, 2)
            }
            file.save()
            
            return Response({
                'annotation': self.get_serializer(annotation).data,
                'progress': {
                    'total_fields': total_fields,
                    'verified_fields': verified_fields,
                    'progress': round(progress, 2)
                }
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['PUT'])
    def update_content(self, request, pk=None):
        """创建新版本（修改内容）"""
        annotation = self.get_object()
        new_json = request.data.get('json_content')
        
        if not new_json:
            return Response(
                {'error': '必须提供 json_content'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 创建历史记录
            AnnotationHistory.objects.create(
                annotation=annotation,
                field_path='root',
                old_value=annotation.json_content,
                new_value=new_json,
                pdf_content=annotation.pdf_content,
                position=annotation.position,
                verification_status='pending',
                change_type='update',
                change_description='更新 JSON 内容',
                modified_by=request.user,
                version=annotation.version + 1
            )
            
            # 更新标注
            annotation.json_content = new_json
            annotation.version += 1
            annotation.save()
            
            return Response(self.get_serializer(annotation).data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['PUT'])
    def edit_field(self, request, pk=None):
        """编辑字段值（不创建新版本）"""
        annotation = self.get_object()
        new_json = request.data.get('json_content')
        
        if not new_json:
            return Response(
                {'error': '必须提供 json_content'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 直接更新当前版本的标注
            annotation.json_content = new_json
            annotation.save()
            
            # 计算新的进度
            total_fields = count_total_fields(new_json)
            verified_fields = count_verified_fields(new_json)
            progress = (verified_fields / total_fields * 100) if total_fields > 0 else 0
            
            # 更新文件进度
            file = annotation.file
            file.metadata = {
                **file.metadata,
                'total_fields': total_fields,
                'verified_fields': verified_fields,
                'progress': round(progress, 2)
            }
            file.save()
            
            return Response({
                'annotation': self.get_serializer(annotation).data,
                'progress': {
                    'total_fields': total_fields,
                    'verified_fields': verified_fields,
                    'progress': round(progress, 2)
                }
            })
            
        except Exception as e:
            return Response(
                {'error': f'编辑失败: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

def traverse_json(obj):
    """递归遍历JSON对象，计算字段数"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield key
            yield from traverse_json(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from traverse_json(item)

def count_verified_fields(json_obj):
    """计算已验证的字段数（带有 -comlhj 后缀的字段或值）"""
    count = 0
    if isinstance(json_obj, dict):
        for key, value in json_obj.items():
            if key.endswith('-comlhj'):
                count += 1
            if isinstance(value, (dict, list)):
                count += count_verified_fields(value)
    elif isinstance(json_obj, list):
        for item in json_obj:
            if isinstance(item, str) and item.endswith('-comlhj'):
                count += 1
            elif isinstance(item, (dict, list)):
                count += count_verified_fields(item)
    return count

def count_total_fields(json_obj):
    """计算总字段数"""
    count = 0
    if isinstance(json_obj, dict):
        for key, value in json_obj.items():
            # 去掉后缀计算总数
            key = key.replace('-comlhj', '')
            count += 1
            if isinstance(value, (dict, list)):
                count += count_total_fields(value)
    elif isinstance(json_obj, list):
        for item in json_obj:
            if isinstance(item, str):
                # 去掉后缀计算总数
                count += 1
            elif isinstance(item, (dict, list)):
                count += count_total_fields(item)
    return count 