from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class File(models.Model):
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('ready', '就绪'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('error', '错误')
    ]

    FILE_TYPES = [
        ('cv', '简历'),
        ('paper', '论文'),
        ('report', '报告'),
        ('other', '其他')
    ]

    pdf_file = models.FileField(upload_to='pdfs/')
    json_file = models.FileField(upload_to='jsons/')
    name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, default='other')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    page_count = models.IntegerField(default=0)
    file_size = models.IntegerField(default=0)  # 以字节为单位
    checksum = models.CharField(max_length=64, null=True, blank=True)  # 设为可选
    metadata = models.JSONField(null=True, blank=True)  # 存储额外元数据
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.name

    def soft_delete(self, user):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
        # 同时软删除相关的标注
        self.annotations.update(is_deleted=True, deleted_at=timezone.now())

class Annotation(models.Model):
    FIELD_ORDER = [
        'personal_info',
        'education',
        'appointments',
        'clinical_activities',
        'clinical_trials',
        'community_services',
        'editorial_services',
        'grant_review_services',
        'grants',
        'honors',
        'patents',
        'presentations',
        'professional_organization_services',
        'publications',
        'teaching_and_training_activities',
        'trainees',
        'university_administrative_services'
    ]

    FIELD_TYPES = [
        ('personal_info', '个人信息'),
        ('education', '教育经历'),
        ('work_experience', '工作经验'),
        ('skills', '技能特长'),
        ('projects', '项目经验'),
        ('certificates', '证书认证'),
        ('languages', '语言能力'),
        ('others', '其他信息')
    ]

    VERIFICATION_STATUS = [
        ('pending', '待验证'),
        ('verified', '已验证'),
        ('incorrect', '不正确'),
        ('missing', '信息缺失'),
        ('redundant', '冗余信息')
    ]

    file = models.ForeignKey(File, related_name='annotations', on_delete=models.CASCADE)
    field_type = models.CharField(max_length=50, choices=FIELD_TYPES)
    field_path = models.CharField(max_length=255)  # 例如: "personal_info.name"
    pdf_content = models.TextField()  # PDF中实际内容
    json_content = models.JSONField()  # JSON中的内容
    position = models.JSONField(null=True, blank=True)  # PDF中的位置信息 {page: 1, x1: 100, y1: 100, x2: 200, y2: 120}
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    is_correct = models.BooleanField(default=False)
    confidence_score = models.FloatField(default=0.0)
    comment = models.TextField(blank=True)
    annotator = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.IntegerField(default=1)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-version']

    def __str__(self):
        return f"Annotation for {self.file.name} by {self.annotator.username}"

    def order_json_content(self):
        """按照预定义的顺序重排 JSON 内容"""
        if not isinstance(self.json_content, dict):
            return self.json_content
            
        ordered_content = {}
        # 按预定义顺序处理字段
        for field in self.FIELD_ORDER:
            if field in self.json_content:
                ordered_content[field] = self.json_content[field]
        
        # 处理其他未在顺序中定义的字段
        for key in self.json_content:
            if key not in ordered_content:
                ordered_content[key] = self.json_content[key]
            
        return ordered_content

    def save(self, *args, **kwargs):
        # 保存前对 JSON 内容进行排序
        if self.json_content:
            self.json_content = self.order_json_content()
        super().save(*args, **kwargs)

class AnnotationHistory(models.Model):
    CHANGE_TYPES = [
        ('create', '创建'),
        ('update', '更新'),
        ('verify', '验证'),
        ('missing', '添加缺失'),
        ('rollback', '回滚')
    ]

    annotation = models.ForeignKey(Annotation, related_name='history', on_delete=models.CASCADE)
    field_path = models.CharField(max_length=255)  # 记录修改的字段路径
    old_value = models.JSONField(null=True)  # 修改前的值
    new_value = models.JSONField()  # 修改后的值
    pdf_content = models.TextField()  # PDF中的实际内容
    position = models.JSONField()  # 位置信息
    verification_status = models.CharField(max_length=20)  # 当时的验证状态
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPES)
    change_description = models.TextField()  # 变更描述
    modified_by = models.ForeignKey(User, on_delete=models.CASCADE)
    modified_at = models.DateTimeField(auto_now_add=True)
    version = models.IntegerField()

    class Meta:
        ordering = ['-version'] 