import traceback,sys
import os
from io import BytesIO
import json
import time
import datetime
from datetime import datetime, timedelta, timezone
import base64
import boto3
from boto3.dynamodb.conditions import Key, Attr
from PIL import Image
from django.db import connection
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from huuurray.post_data.models import PostData
from huuurray.hr_user.models import HrUser


# 変数定義
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('Huuurray_Dev_Nice')


@csrf_exempt
def upsert(request):
    """投稿データの新規作成/更新"""
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
            or body.get("content") is None:
            error_result["message"] = "NO DATA"
            return JsonResponse(error_result)
        else:
            username = body.get("username")
            content = body.get("content")
            try:
                if body.get("id") is None:
                    PostData.objects.create(
                        username=HrUser(username=username),
                        content=content
                    )
                else:
                    post_id = body.get("id")
                    record = PostData.objects.get(id=post_id)
                    record.content = content
                    record.save()
                return JsonResponse(ok_result)
            except Exception as e:
                ex, ms, tb = sys.exc_info()
                error_result["message"] = format(ms)
                return JsonResponse(error_result)


@csrf_exempt
def get_post_data(request):
    """投稿データの取得"""
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
            or body.get("feedFlg") is None\
            or body.get("favoriteFlg") is None\
            or body.get("page") is None:
            error_result["message"] = "NO DATA"
            return JsonResponse(error_result)
        else:
            page_cnt = 10
            page = int(body.get("page"))
            offset = str(page * page_cnt)
            username = body.get("username")
            feed_flg = body.get("feedFlg")
            favorite_flg = body.get("favoriteFlg")
            if feed_flg and favorite_flg:
                add_join_pre = """
                    INNER JOIN
                    (
                        SELECT *
                        FROM hr_user_favoriteuser
                        WHERE from_username_id = \"%s\"
                    ) as favorite
                    ON user.username = favorite.to_username_id
                """
                add_join = add_join_pre % username
                add_where = ""
            elif feed_flg:
                add_join = ""
                add_where = ""
            else:
                add_join = ""
                add_where = "AND user.username = \"%s\"" % username
            sql = """
                SELECT
                    post.id as id,
                    post.content as content,
                    post.created_at as created_at,
                    post.modified_at as modified_at,
                    user.username as username,
                    user.disp_name as disp_name,
                    user.account_image as account_image,
                    user.wp_on as wp_on,
                    user.wp1_name as wp1_name
                FROM
                    hr_user_hruser as user
                    %s
                    INNER JOIN
                    post_data_postdata as post
                    ON user.username = post.username_id
                WHERE
                    user.delete_flg = '0' AND
                    post.delete_flg = '0' 
                    %s
                ORDER BY
                    post.modified_at DESC
                LIMIT %s
                OFFSET %s ;
                """
            try:
                post_datas = exec_query(sql % (add_join, add_where, str(page_cnt), offset))
                post_datas_dict = list(post_datas)
                for row in post_datas_dict:
                    all_nice = all_nice_query(row["id"])
                    row["favorite_cnt"] = all_nice["Count"]
                    row["favorite"] = False
                    if username != "":
                        one_nice = one_nice_query(row["id"], username)
                        if one_nice["Count"] > 0:
                            row["favorite"] = True                        
                ok_result["data"] = post_datas_dict
                return JsonResponse(ok_result, safe=False)
            except Exception as e:
                ex, ms, tb = sys.exc_info()
                error_result["message"] = format(ms)
                return JsonResponse(error_result)


def exec_query(sql):
    with connection.cursor() as c:
        c.execute(sql)
        columns = [col[0] for col in c.description]
        return [
            dict(zip(columns, row))
            for row in c.fetchall()
        ]


@csrf_exempt
def nice(request):
    """いいね！の作成/削除"""
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
        if body.get("id") is None\
            or body.get("username") is None\
            or body.get("favorite") is None:
            error_result["message"] = "NO DATA"
            return JsonResponse(error_result)
        else:
            try:
                post_data_id = body.get("id")
                username = body.get("username")
                favorite = body.get("favorite")
                JST = timezone(timedelta(hours=+9), 'JST')
                now = datetime.now(JST)
                time_stamp = int(now.strftime('%s'))
                if favorite:
                    insert(post_data_id, username, time_stamp)
                else:
                    delete(post_data_id, username)
                return JsonResponse(ok_result)
            except Exception as e:
                ex, ms, tb = sys.exc_info()
                error_result["message"] = format(ms)
                return JsonResponse(error_result)


@csrf_exempt
def get_nice(request):
    """いいね！の取得"""
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
        if body.get("id") is None\
            or body.get("page") is None:
            error_result["message"] = "NO DATA"
            return JsonResponse(error_result)
        else:
            page_cnt = 20
            page = int(body.get("page"))
            offset = page * page_cnt
            limit = offset + page_cnt
            try:
                post_data_id = body.get("id")
                all_nice = all_nice_query(post_data_id)
                list_cnt = len(all_nice["Items"])
                in_list = []
                for i in range(offset, limit):
                    if i >= list_cnt:
                        break
                    in_list.append(all_nice["Items"][i]["username"])
                hr_users = HrUser.objects.filter(
                    username__in=in_list
                ).exclude(
                    delete_flg="1"
                ).values(
                    "username",
                    "disp_name",
                    "account_image",
                    "wp_on",
                    "wp1_name"
                )
                ok_result['data'] = list(hr_users)
                return JsonResponse(ok_result)
            except Exception as e:
                ex, ms, tb = sys.exc_info()
                error_result["message"] = format(ms)
                return JsonResponse(error_result)


def insert(post_data_id, username, time_stamp):
    """いいねデータをDynamoDBにインサート"""
    table.put_item(
        Item={
            "post_data_id": post_data_id,
            "username": username,
            "created_at": time_stamp
        }
    )


def delete(post_data_id, username):
    """いいねデータをDynamoDBから削除"""
    table.delete_item(Key={'post_data_id': post_data_id, 'username': username})


def all_nice_query(post_data_id):
    """投稿に対する全てのいいね！を取得"""
    data = table.query(
        KeyConditionExpression=Key('post_data_id').eq(post_data_id)
    )
    return data


def one_nice_query(post_data_id, username):
    """投稿に対する一件のいいね！を取得"""
    data = table.query(
        KeyConditionExpression=Key('post_data_id').eq(post_data_id) & Key('username').eq(username)
    )
    return data
