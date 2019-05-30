from django.db import models
from huuurray.hr_user.models import HrUser


class ToPointDay(models.Model):
    """hr_sp_topointday"""
    id = models.AutoField('もらったポイントID', primary_key=True)
    username = models.ForeignKey(HrUser, on_delete=models.CASCADE)
    date = models.DateField('日付')
    point = models.IntegerField('ポイント')
    delete_flg = models.CharField('削除フラグ', max_length=1, default='0')
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    modified_at = models.DateTimeField('更新日時', auto_now=True)

    def __str__(self):
        return self.username


class FromPointDay(models.Model):
    """hr_sp_frompointday"""
    id = models.AutoField('送ったポイントID', primary_key=True)
    username = models.ForeignKey(HrUser, on_delete=models.CASCADE)
    date = models.DateField('日付')
    point = models.IntegerField('ポイント')
    delete_flg = models.CharField('削除フラグ', max_length=1, default='0')
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    modified_at = models.DateTimeField('更新日時', auto_now=True)

    def __str__(self):
        return self.username