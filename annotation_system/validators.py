from django.core.exceptions import ValidationError
import json

def validate_cv_json(json_content):
    """
    验证简历JSON格式，基于Sean Wu CV的结构
    """
    try:
        # 检查是否为空
        if not json_content:
            raise ValidationError('JSON内容不能为空')
            
        # 检查是否为字典类型
        if not isinstance(json_content, dict):
            raise ValidationError('JSON内容必须是对象类型')
            
        # 定义必要字段
        required_fields = [
            'personal_info',
            'education',
            'appointments',
            'honors',
            'publications',
            'grants'
        ]
        
        missing_fields = [field for field in required_fields if field not in json_content]
        if missing_fields:
            raise ValidationError(f'缺少以下必要字段: {", ".join(missing_fields)}')
            
        # 验证 personal_info 字段
        if 'personal_info' in json_content:
            personal_info = json_content['personal_info']
            if not isinstance(personal_info, dict):
                raise ValidationError('personal_info必须是对象类型')
                
            # 检查个人信息必要字段
            required_personal_fields = ['name', 'title', 'address', 'contact_info']
            missing_personal_fields = [field for field in required_personal_fields 
                                     if field not in personal_info]
            if missing_personal_fields:
                raise ValidationError(f'personal_info缺少以下字段: {", ".join(missing_personal_fields)}')
                
            # 验证联系信息
            if not isinstance(personal_info['contact_info'], dict):
                raise ValidationError('contact_info必须是对象类型')
        
        # 验证 education 字段
        if 'education' in json_content:
            education = json_content['education']
            if not isinstance(education, dict):
                raise ValidationError('education必须是对象类型')
                
        # 验证 appointments 字段
        if 'appointments' in json_content:
            appointments = json_content['appointments']
            if not isinstance(appointments, dict):
                raise ValidationError('appointments必须是对象类型')
                
        # 验证 publications 字段
        if 'publications' in json_content:
            publications = json_content['publications']
            if not isinstance(publications, dict):
                raise ValidationError('publications必须是对象类型')
                
            if 'peer_reviewed_articles' in publications:
                if not isinstance(publications['peer_reviewed_articles'], list):
                    raise ValidationError('peer_reviewed_articles必须是数组类型')
                    
            if 'book_chapters' in publications:
                if not isinstance(publications['book_chapters'], list):
                    raise ValidationError('book_chapters必须是数组类型')
                
    except ValidationError as e:
        raise e
    except Exception as e:
        raise ValidationError(f'JSON格式验证失败: {str(e)}') 