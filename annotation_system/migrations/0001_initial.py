# Generated by Django 5.1.6 on 2025-02-19 07:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Annotation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field_type', models.CharField(choices=[('personal_info', '个人信息'), ('education', '教育经历'), ('work_experience', '工作经验'), ('skills', '技能特长'), ('projects', '项目经验'), ('certificates', '证书认证'), ('languages', '语言能力'), ('others', '其他信息')], max_length=50)),
                ('field_path', models.CharField(max_length=255)),
                ('pdf_content', models.TextField()),
                ('json_content', models.JSONField()),
                ('position', models.JSONField()),
                ('verification_status', models.CharField(choices=[('pending', '待验证'), ('verified', '已验证'), ('incorrect', '不正确'), ('missing', '信息缺失'), ('redundant', '冗余信息')], default='pending', max_length=20)),
                ('is_correct', models.BooleanField(default=False)),
                ('confidence_score', models.FloatField(default=0.0)),
                ('comment', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('version', models.IntegerField(default=1)),
                ('annotator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-version'],
            },
        ),
        migrations.CreateModel(
            name='AnnotationHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field_path', models.CharField(max_length=255)),
                ('old_value', models.JSONField(null=True)),
                ('new_value', models.JSONField()),
                ('pdf_content', models.TextField()),
                ('position', models.JSONField()),
                ('verification_status', models.CharField(max_length=20)),
                ('change_type', models.CharField(choices=[('create', '创建'), ('update', '更新'), ('verify', '验证'), ('missing', '添加缺失'), ('rollback', '回滚')], max_length=20)),
                ('change_description', models.TextField()),
                ('modified_at', models.DateTimeField(auto_now_add=True)),
                ('version', models.IntegerField()),
                ('annotation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='annotation_system.annotation')),
                ('modified_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-version'],
            },
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pdf_file', models.FileField(upload_to='pdfs/')),
                ('json_file', models.FileField(upload_to='jsons/')),
                ('name', models.CharField(max_length=255)),
                ('file_type', models.CharField(choices=[('cv', '简历'), ('paper', '论文'), ('report', '报告'), ('other', '其他')], default='other', max_length=20)),
                ('status', models.CharField(choices=[('pending', '待处理'), ('ready', '就绪'), ('processing', '处理中'), ('completed', '已完成'), ('error', '错误')], default='pending', max_length=20)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('page_count', models.IntegerField(default=0)),
                ('file_size', models.IntegerField(default=0)),
                ('checksum', models.CharField(blank=True, max_length=64, null=True)),
                ('metadata', models.JSONField(blank=True, null=True)),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.AddField(
            model_name='annotation',
            name='file',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='annotations', to='annotation_system.file'),
        ),
    ]
