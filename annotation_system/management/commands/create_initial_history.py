from django.core.management.base import BaseCommand
from annotation_system.models import Annotation, AnnotationHistory

class Command(BaseCommand):
    help = '为所有没有历史记录的标注创建初始历史记录'

    def handle(self, *args, **options):
        annotations = Annotation.objects.all()
        count = 0
        
        for annotation in annotations:
            # 检查是否已有历史记录
            if not annotation.history.exists():
                AnnotationHistory.objects.create(
                    annotation=annotation,
                    field_path=annotation.field_path,
                    old_value=None,
                    new_value=annotation.json_content,
                    pdf_content=annotation.pdf_content,
                    position=annotation.position,
                    verification_status=annotation.verification_status,
                    change_type='create',
                    change_description='创建初始历史记录',
                    modified_by=annotation.annotator,
                    version=1
                )
                count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'成功创建 {count} 条初始历史记录')
        ) 