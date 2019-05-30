import traceback,sys
import os
from io import BytesIO
import json
import time
import datetime
from datetime import datetime, timedelta, timezone
import base64
import boto3
from PIL import Image
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from huuurray.hr_user.models import HrUser, FavoriteUser
from huuurray.post_data.views import exec_query


@csrf_exempt
def upsert(request):
    """ユーザの新規作成/更新"""
    # 返り値
    error_result = {"statusCode": "400"}
    # POSTのみ実行
    if request.method != "POST":
        error_result["message"] = "NOT POST"
        return JsonResponse(error_result)
    else:
        # BodyのJsonをロード
        body_json = (request.body).decode('utf-8')
        body = json.loads(body_json)
        # Key項目の存在確認
        if body.get("username") is None:
            error_result["message"] = "NO DATA"
            return JsonResponse(error_result)
        else:
            try:
                HrUser.objects.update_or_create(
                    username=body.get("username"),
                    defaults=body
                )
                ok_result = body
                ok_result["statusCode"] = "200"
                return JsonResponse(ok_result)
            except Exception as e:
                ex, ms, tb = sys.exc_info()
                error_result["message"] = format(ms)
                return JsonResponse(error_result)


@csrf_exempt
def image_upsert(request):
    """画像の新規作成/更新"""
    # 返り値
    ok_result = {"statusCode": "200"}
    error_result = {"statusCode": "400"}
    # POSTのみ実行
    if request.method != "POST":
        error_result["message"] = "NOT POST"
        return JsonResponse(error_result)
    else:
        # BodyのJsonをロード
        body_json = (request.body).decode('utf-8')
        body = json.loads(body_json)
        # Key項目の存在確認
        if body.get("username") is None \
            or body.get("imageType") is None:
            error_result["message"] = "NO DATA"
            return JsonResponse(error_result)
        else:
            username = body.get("username")
            image_type = body.get("imageType")
            image_col_name = image_type + "_image"
            try:
                # 画像を一旦サーバー内に保存
                image = base64.b64decode(body.get("image"))
                image_data = BytesIO(image)
                img = Image.open(image_data)
                t = time.time()
                dir_path = "/tmp/image/"
                img_name = username + str(t) + ".png"
                img.save(dir_path + img_name, "PNG")
                # S3にアップロード
                s3 = boto3.resource("s3")
                bucket = s3.Bucket("huuurraytestdev")
                bucket_path = image_col_name + "/"
                bucket.upload_file(dir_path + img_name, bucket_path + img_name)
                # 画像の名前をDBに保存
                HrUser.objects.update_or_create(
                    username=username,
                    defaults={
                        "username": username,
                        image_col_name: img_name}
                )
                # 添付画像を削除
                os.remove(dir_path + img_name)
                # 戻り値をセット
                ok_result["username"] = username
                ok_result["imageType"] = image_type
                ok_result["image"] = img_name
                return JsonResponse(ok_result)
            except Exception as e:
                ex, ms, tb = sys.exc_info()
                error_result["message"] = format(ms)
                return JsonResponse(error_result)


@csrf_exempt
def get_user_data(request):
    """ユーザデータの取得"""
    # 返り値
    ok_result = {"statusCode": "200"}
    error_result = {"statusCode": "400"}
    # POSTのみ実行
    if request.method != "POST":
        error_result["message"] = "NOT POST"
        return JsonResponse(error_result)
    else:
        # BodyのJsonをロード
        body_json = (request.body).decode('utf-8')
        body = json.loads(body_json)
        # Key項目の存在確認
        if body.get("updatedAt") is None:
            error_result["message"] = "NO DATA"
            return JsonResponse(error_result)
        else:
            try:
                if body.get("updatedAt") != "":
                    updated_dt = datetime.strptime(body.get("updatedAt"), '%Y-%m-%d %H:%M:%S')
                    td_30m = timedelta(minutes=30)
                    updated_dt_m30m = updated_dt - td_30m
                    hr_users = HrUser.objects.filter(
                        modified_at__gte=updated_dt_m30m
                    ).exclude(
                        delete_flg="1"
                    )
                else:
                    hr_users = HrUser.objects.exclude(delete_flg="1")
                ok_result["data"] = list(hr_users.values())
                return JsonResponse(ok_result, safe=False)
            except Exception as e:
                ex, ms, tb = sys.exc_info()
                error_result["message"] = format(ms)
                return JsonResponse(error_result)


@csrf_exempt
def get_ranking(request):
    """ランキングデータの取得"""
    # 返り値
    ok_result = {"statusCode": "200"}
    error_result = {"statusCode": "400"}
    # POSTのみ実行
    if request.method != "POST":
        error_result["message"] = "NOT POST"
        return JsonResponse(error_result)
    else:
        # BodyのJsonをロード
        body_json = (request.body).decode('utf-8')
        body = json.loads(body_json)
        # Key項目の存在確認
        if body.get("position") is None\
            or body.get("page") is None:
            error_result["message"] = "NO DATA"
            return JsonResponse(error_result)
        else:
            page_cnt = 10
            page = int(body.get("page"))
            offset = str(page * page_cnt)
            try:
                position = body.get("position")
                JST = timezone(timedelta(hours=+9), 'JST')
                now = datetime.now(JST)
                s_day = datetime(
                    now.year,
                    now.month,
                    1,
                    0, 0, 0, 0)
                s_day_yymmdd = s_day.strftime('%Y-%m-%d')
                month = now.month + 1
                year = now.year
                if now.month == 12:
                    month = 1
                    year = year + 1
                e_day = datetime(
                    year,
                    month,
                    1,
                    0, 0, 0, 0)
                e_day_yymmdd = e_day.strftime('%Y-%m-%d')
                sp_sql = """
                    SELECT DISTINCT
                        user.username as username,
                        user.disp_name as disp_name,
                        user.account_image as account_image,
                        user.profile as profile,
                        sum(point.point) as s_point,
                        user.wp_on as wp_on,
                        user.wp1_name as wp1_name,
                        user.wp1_category as wp1_category
                    FROM
                        (
                            SELECT *
                            FROM hr_user_hruser
                            WHERE delete_flg = '0'
                        ) as user
                        INNER JOIN
                        %s as point
                        on user.username = point.username_id
                    GROUP BY
                        user.username 
                    ORDER BY
                        s_point DESC,
                        user.created_at ASC
                    LIMIT %s
                    OFFSET %s ;
                """
                table_type = ""
                if position == 0:
                    table_type = "hr_sp_topointday"
                elif position == 1:
                    table_type_pre = """(
                        SELECT *
                        FROM hr_sp_topointday
                        WHERE
                            date >= \"%s\" AND
                            date < \"%s\")
                      """
                    table_type = table_type_pre % (s_day_yymmdd, e_day_yymmdd)
                elif position == 2:
                    table_type = "hr_sp_frompointday"
                elif position == 3:
                    table_type_pre = """(
                        SELECT *
                        FROM hr_sp_frompointday
                        WHERE
                            date >= \"%s\" AND
                            date < \"%s\")
                      """
                    table_type = table_type_pre % (s_day_yymmdd, e_day_yymmdd)
                ranking_obj = exec_query(sp_sql % (table_type, str(page_cnt), offset))
                ok_result["data"] = list(ranking_obj)
                return JsonResponse(ok_result, safe=False)
            except Exception as e:
                ex, ms, tb = sys.exc_info()
                error_result["message"] = format(ms)
                return JsonResponse(error_result)


@csrf_exempt
def follow_user(request):
    """お気に入り登録"""
    # 返り値
    ok_result = {"statusCode": "200"}
    error_result = {"statusCode": "400"}
    # POSTのみ実行
    if request.method != "POST":
        error_result["message"] = "NOT POST"
        return JsonResponse(error_result)
    else:
        # BodyのJsonをロード
        body_json = (request.body).decode('utf-8')
        body = json.loads(body_json)
        # Key項目の存在確認
        if body.get("to_username") is None\
            or body.get("from_username") is None\
            or body.get("flg") is None:
            error_result["message"] = "NO DATA"
            return JsonResponse(error_result)
        else:
            to_username = body.get("to_username")
            from_username = body.get("from_username")
            flg = body.get("flg")
            try:
                old_data_cnt = FavoriteUser.objects.filter(
                    to_username=HrUser(username=to_username),
                    from_username=HrUser(username=from_username)).count()
                if old_data_cnt == 0 and flg:
                    FavoriteUser.objects.create(
                        to_username=HrUser(username=to_username),
                        from_username=HrUser(username=from_username)
                    )
                elif old_data_cnt != 0 and not flg:
                    FavoriteUser.objects.filter(
                        to_username=HrUser(username=to_username),
                        from_username=HrUser(username=from_username)).delete()

                return JsonResponse(ok_result)
            except Exception as e:
                ex, ms, tb = sys.exc_info()
                error_result["message"] = format(ms)
                return JsonResponse(error_result)


@csrf_exempt
def get_follow_user(request):
    """お気に入り登録者一覧の取得"""
       # 返り値
    ok_result = {"statusCode": "200"}
    error_result = {"statusCode": "400"}
    # POSTのみ実行
    if request.method != "POST":
        error_result["message"] = "NOT POST"
        return JsonResponse(error_result)
    else:
        # BodyのJsonをロード
        body_json = (request.body).decode('utf-8')
        body = json.loads(body_json)
        # Key項目の存在確認
        if body.get("username") is None\
            or body.get("flg") is None\
            or body.get("page") is None:
            error_result["message"] = "NO DATA"
            return JsonResponse(error_result)
        else:
            username = body.get("username")
            flg = body.get("flg")
            page_cnt = 20
            page = int(body.get("page"))
            offset = str(page * page_cnt)
            try:
                sql = """
                    SELECT
                        user.username as username,
                        user.disp_name as disp_name,
                        user.account_image as account_image,
                        user.wp_on as wp_on,
                        user.wp1_name as wp1_name
                    FROM
                        (
                            SELECT *
                            FROM hr_user_hruser
                            WHERE delete_flg = '0'
                        ) as user
                        INNER JOIN
                        (
                            SELECT *
                            FROM hr_user_favoriteuser
                            WHERE %s = \"%s\"
                        ) as flw
                        on user.username = flw.%s
                    ORDER BY
                        user.modified_at ASC
                    LIMIT %s
                    OFFSET %s ;
                """
                if flg:
                    fil_col = "to_username_id"
                    rel_col = "from_username_id"
                else:
                    fil_col = "from_username_id"
                    rel_col = "to_username_id"
                follow_obj = exec_query(sql % (fil_col, username, rel_col, str(page_cnt), offset))
                ok_result["data"] = list(follow_obj)
                return JsonResponse(ok_result)
            except Exception as e:
                ex, ms, tb = sys.exc_info()
                error_result["message"] = format(ms)
                return JsonResponse(error_result)
