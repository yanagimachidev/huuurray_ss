"""This is a hr_message models program"""
from django.db import models
from huuurray.hr_user.models import HrUser


class HrMessage(models.Model):
    """hr_message_hrmessage"""
    id = models.AutoField('メッセージID', primary_key=True)
    to_username = models.ForeignKey(HrUser, on_delete=models.CASCADE, related_name='to_me_username_rel')
    from_username = models.ForeignKey(HrUser, on_delete=models.CASCADE, related_name='from_me_username_rel')
    content = models.TextField('内容')
    delete_flg = models.CharField('削除フラグ', max_length=1, default='0')
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    modified_at = models.DateTimeField('更新日時', auto_now=True)

    def __str__(self):
        return self.id
