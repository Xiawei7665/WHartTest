from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Project, ProjectMember, ProjectCredential
from accounts.serializers import UserDetailSerializer


class ProjectCredentialSerializer(serializers.ModelSerializer):
    """项目凭据序列化器"""
    password = serializers.CharField(write_only=True, allow_blank=True, required=False, help_text='登录密码')

    class Meta:
        model = ProjectCredential
        fields = ['id', 'system_url', 'username', 'password', 'user_role', 'created_at']
        read_only_fields = ['created_at']
        extra_kwargs = {
            'system_url': {'help_text': '系统访问地址（如 https://test.example.com）'},
            'username': {'help_text': '登录账号'},
            'user_role': {'help_text': '如"管理员"、"普通用户"、"审核员"等'}
        }


class ProjectMemberSerializer(serializers.ModelSerializer):
    """项目成员序列化器"""
    user_detail = UserDetailSerializer(source='user', read_only=True)

    class Meta:
        model = ProjectMember
        fields = ['id', 'user', 'user_detail', 'role', 'joined_at']
        read_only_fields = ['joined_at']


class ProjectSerializer(serializers.ModelSerializer):
    """项目基本信息序列化器"""
    creator_detail = UserDetailSerializer(source='creator', read_only=True)
    credentials = ProjectCredentialSerializer(many=True, required=False)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'creator', 'creator_detail', 'created_at', 'updated_at', 'credentials']
        read_only_fields = ['created_at', 'updated_at', 'creator']

    def validate_name(self, value):
        """验证项目名称唯一性"""
        if self.instance is None and Project.objects.filter(name=value).exists():
            raise serializers.ValidationError("项目名称已存在")
        elif self.instance and self.instance.name != value and Project.objects.filter(name=value).exists():
            raise serializers.ValidationError("项目名称已存在")
        return value

    def create(self, validated_data):
        credentials_data = validated_data.pop('credentials', [])
        project = Project.objects.create(**validated_data)
        for credential_data in credentials_data:
            ProjectCredential.objects.create(project=project, **credential_data)
        return project

    def update(self, instance, validated_data):
        credentials_data = validated_data.pop('credentials', None)
        
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.save()

        if credentials_data is not None:
            instance.credentials.all().delete()
            for credential_data in credentials_data:
                ProjectCredential.objects.create(project=instance, **credential_data)

        return instance


class ProjectDetailSerializer(ProjectSerializer):
    """项目详细信息序列化器，包含成员信息"""
    members = ProjectMemberSerializer(many=True, read_only=True)

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ['members']


class ProjectMemberCreateSerializer(serializers.ModelSerializer):
    """创建项目成员的序列化器"""
    user_id = serializers.IntegerField(write_only=True, help_text="用户ID")

    class Meta:
        model = ProjectMember
        fields = ['user_id', 'role']

    def validate_user_id(self, value):
        """验证用户ID是否存在"""
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("用户不存在")
        return value

    def validate(self, attrs):
        """验证用户是否已经是项目成员"""
        project = self.context['project']
        user_id = attrs['user_id']

        if ProjectMember.objects.filter(project=project, user_id=user_id).exists():
            raise serializers.ValidationError({"user_id": "该用户已经是项目成员"})

        return attrs

    def create(self, validated_data):
        project = self.context['project']
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)
        return ProjectMember.objects.create(project=project, user=user, **validated_data)
