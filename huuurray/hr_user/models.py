from django.db import models


class HrUser(models.Model):
    """hr_user_hruser"""
    username = models.CharField('ユーザー名', max_length=20, primary_key=True)
    disp_name = models.CharField('表示名', max_length=100, null=True, blank=True)
    sex = models.CharField('性別', max_length=1, null=True, blank=True)
    birthday = models.DateField('誕生日', null=True)
    profile = models.TextField('プロフィール文', null=True, blank=True)
    account_image = models.CharField('アカウント画像', max_length=100, null=True, blank=True)
    back_image = models.CharField('背景画像', max_length=100, null=True, blank=True)
    wp_on = models.CharField('有効WP', max_length=1, default='0')
    wp1_name = models.CharField('WP1名前', max_length=100, null=True, blank=True)
    wp1_category = models.CharField('WP1店舗種別', max_length=30, null=True, blank=True)
    wp1_url = models.CharField('WP1URL', max_length=200, null=True, blank=True)
    wp1_lat = models.DecimalField('WP1緯度', max_digits=10, decimal_places=7, null=True)
    wp1_lng = models.DecimalField('WP1経度', max_digits=10, decimal_places=7, null=True)
    wp1_lat_sort = models.DecimalField('緯度順', max_digits=6, decimal_places=3, null=True)
    wp1_lng_sort = models.DecimalField('経度順', max_digits=6, decimal_places=3, null=True)
    wp1_latlng_sort = models.DecimalField('緯度経度順', max_digits=10, decimal_places=4, null=True)
    wp1_image = models.CharField('WP1画像', max_length=100, null=True, blank=True)
    """
    wp2_name = models.CharField('WP2名前', max_length=100, null=True, blank=True)
    wp2_category = models.CharField('WP2店舗種別', max_length=30, null=True, blank=True)
    wp2_url = models.CharField('WP2URL', max_length=200, null=True, blank=True)
    wp2_lat = models.DecimalField('WP2緯度', max_digits=10, decimal_places=7, null=True)
    wp2_lng = models.DecimalField('WP2経度', max_digits=10, decimal_places=7, null=True)
    wp2_image = models.CharField('WP2画像', max_length=100, null=True, blank=True)
    wp3_name = models.CharField('WP3名前', max_length=100, null=True, blank=True)
    wp3_category = models.CharField('WP3店舗種別', max_length=30, null=True, blank=True)
    wp3_url = models.CharField('WP3URL', max_length=200, null=True, blank=True)
    wp3_lat = models.DecimalField('WP3緯度', max_digits=10, decimal_places=7, null=True)
    wp3_lng = models.DecimalField('WP3経度', max_digits=10, decimal_places=7, null=True)
    wp3_image = models.CharField('WP3画像', max_length=100, null=True, blank=True)
    """
    delete_flg = models.CharField('削除フラグ', max_length=1, default='0')
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    modified_at = models.DateTimeField('更新日時', auto_now=True)

    def __str__(self):
        return self.username


class FavoriteUser(models.Model):
    """hr_user_favoriteuser"""
    id = models.AutoField('お気に入り登録ID', primary_key=True)
    to_username = models.ForeignKey(HrUser, on_delete=models.CASCADE, related_name='to_username_rel')
    from_username = models.ForeignKey(HrUser, on_delete=models.CASCADE, related_name='from_username_rel')
    delete_flg = models.CharField('削除フラグ', max_length=1, default='0')
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    modified_at = models.DateTimeField('更新日時', auto_now=True)

    def __str__(self):
        return self.id
