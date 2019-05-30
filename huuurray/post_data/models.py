from django.db import models
from huuurray.hr_user.models import HrUser


class PostData(models.Model):
    """post_data_postdata"""
    id = models.AutoField('投稿ID', primary_key=True)
    username = models.ForeignKey(HrUser, on_delete=models.CASCADE)
    content = models.TextField('内容')
    image1 = models.CharField('画像１', max_length=100, null=True, blank=True)
    lat = models.DecimalField('投稿緯度', max_digits=10, decimal_places=7, null=True)
    lng = models.DecimalField('投稿経度', max_digits=10, decimal_places=7, null=True)
    delete_flg = models.CharField('削除フラグ', max_length=1, default='0')
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    modified_at = models.DateTimeField('更新日時', auto_now=True)

    def __str__(self):
        return self.id
