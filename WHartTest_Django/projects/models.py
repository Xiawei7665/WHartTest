from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class Project(models.Model):
    """
    项目模型，包含项目的基本信息
    """
    name = models.CharField(_('项目名称'), max_length=100, unique=True)
    description = models.TextField(_('项目描述'), blank=True)
    creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_projects',
        verbose_name=_('创建人')
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)

    class Meta:
        verbose_name = _('项目')
        verbose_name_plural = _('项目')
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class ProjectCredential(models.Model):
    """
    项目凭据模型，存储项目的系统访问信息
    一个项目可以有多个凭据，用于不同角色的登录
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='credentials',
        verbose_name=_('项目')
    )
    system_url = models.URLField(_('项目地址'), max_length=255, blank=True, help_text='系统访问地址（如 https://test.example.com）')
    username = models.CharField(_('用户名'), max_length=100, blank=True, help_text='登录账号')
    password = models.CharField(_('密码'), max_length=255, blank=True, help_text='登录密码')
    user_role = models.CharField(_('角色'), max_length=50, blank=True, help_text='如"管理员"、"普通用户"、"审核员"等')
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)

    class Meta:
        verbose_name = _('项目凭据')
        verbose_name_plural = _('项目凭据')
        ordering = ['project', 'user_role']

    def __str__(self):
        return f"{self.project.name} - {self.user_role or self.username}"


class ProjectMember(models.Model):
    """
    项目成员关系模型，定义用户与项目的关系
    """
    ROLE_CHOICES = (
        ('owner', _('拥有者')),
        ('admin', _('管理员')),
        ('member', _('成员')),
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name=_('项目')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='project_memberships',
        verbose_name=_('用户')
    )
    role = models.CharField(
        _('角色'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='member'
    )
    joined_at = models.DateTimeField(_('加入时间'), auto_now_add=True)

    class Meta:
        verbose_name = _('项目成员')
        verbose_name_plural = _('项目成员')
        unique_together = ('project', 'user')  # 确保一个用户在一个项目中只有一个角色
        ordering = ['project', 'role', 'joined_at']

    def __str__(self):
        return f"{self.user.username} - {self.project.name} ({self.get_role_display()})"
