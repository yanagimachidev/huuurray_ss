import traceback,sys
import json
import time
import datetime
from datetime import datetime, timedelta, timezone
import boto3
from boto3.dynamodb.conditions import Key, Attr
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from huuurray.hr_user.models import HrUser
from huuurray.hr_message.models import HrMessage
from huuurray.post_data.views import exec_query


# 変数定義
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('Huuurray_Dev_Thanks_Nice')


@csrf_exempt
def get_message(request):
    """１ユーザーに関連するメッセージデータの取得"""
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
        if body.get("updatedAt") is None \
            or body.get("username") is None:
            error_result["message"] = "NO DATA"
            return JsonResponse(error_result)
        else:
            username = body.get("username")
            try:
                if body.get("updatedAt") != "":
                    updated_dt = datetime.strptime(body.get("updatedAt"), '%Y-%m-%d %H:%M:%S')
                    td_30m = timedelta(minutes=30)
                    updated_dt_m30m = updated_dt - td_30m
                    # 最終取得から30分以内に受け取ったメッセージを再取得
                    hr_messages = HrMessage.objects.filter(
                        Q(modified_at__gte=updated_dt_m30m),
                        (Q(to_username=username) | Q(from_username=username))
                    ).exclude(
                        delete_flg="1"
                    )
                else:
                    # 自分に関連するメッセージを全件取得
                    hr_messages = HrMessage.objects.filter(
                        Q(to_username=username) | Q(from_username=username)
                    ).exclude(
                        delete_flg="1"
                    )
                messages_dict = list(hr_messages.values())
                for row in messages_dict:
                    all_nice = all_nice_query(row["id"])
                    row["favorite_cnt"] = all_nice["Count"]
                    row["favorite"] = False
                    if username != "":
                        one_nice = one_nice_query(row["id"], username)
                        if one_nice["Count"] > 0:
                            row["favorite"] = True                        
                ok_result["data"] = messages_dict
                return JsonResponse(ok_result, safe=False)
            except Exception as e:
                ex, ms, tb = sys.exc_info()
                error_result["message"] = format(ms)
                return JsonResponse(error_result)


@csrf_exempt
def get_message_feed(request):
    """メッセージフィードデータの取得"""
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
            or body.get("favoriteFlg") is None\
            or body.get("page") is None:
            error_result["message"] = "NO DATA"
            return JsonResponse(error_result)
        else:
            page_cnt = 10
            page = int(body.get("page"))
            offset = str(page * page_cnt)
            username = body.get("username")
            favorite_flg = body.get("favoriteFlg")
            add_join = ""
            if favorite_flg:
                add_join_pre = """
                    INNER JOIN
                    (
                        SELECT *
                        FROM hr_user_favoriteuser
                        WHERE from_username_id = \"%s\"
                    ) as favorite
                    ON to_user.username = favorite.to_username_id
                """
                add_join = add_join_pre % username

            sql = """
                SELECT
                    message.id as id,
                    message.content as content,
                    message.created_at as created_at,
                    message.modified_at as modified_at,
                    to_user.username as to_username,
                    to_user.disp_name as to_disp_name,
                    to_user.account_image as to_account_image,
                    to_user.wp_on as to_wp_on,
                    to_user.wp1_name as to_wp1_name,
                    from_user.username as from_username,
                    from_user.disp_name as from_disp_name,
                    from_user.account_image as from_account_image,
                    from_user.wp_on as from_wp_on,
                    from_user.wp1_name as from_wp1_name
                FROM
                    hr_user_hruser as to_user
                    %s
                    INNER JOIN
                    hr_message_hrmessage as message
                    ON to_user.username = message.to_username_id
                    INNER JOIN
                    hr_user_hruser as from_user
                    ON from_user.username = message.from_username_id
                WHERE
                    to_user.delete_flg = '0' AND
                    from_user.delete_flg = '0' AND
                    message.delete_flg = '0' 
                ORDER BY
                    message.created_at DESC
                LIMIT %s
                OFFSET %s ;
                """
            try:
                messages = exec_query(sql % (add_join, str(page_cnt), offset))
                messages_dict = list(messages)
                for row in messages_dict:
                    all_nice = all_nice_query(row["id"])
                    row["favorite_cnt"] = all_nice["Count"]
                    row["favorite"] = False
                    if username != "":
                        one_nice = one_nice_query(row["id"], username)
                        if one_nice["Count"] > 0:
                            row["favorite"] = True                        
                ok_result["data"] = messages_dict
                return JsonResponse(ok_result, safe=False)
            except Exception as e:
                ex, ms, tb = sys.exc_info()
                error_result["message"] = format(ms)
                return JsonResponse(error_result)


@csrf_exempt
def upsert(request):
    """メッセージデータの新規作成/更新"""
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
        if body.get("to_username") is None \
            or body.get("from_username") is None \
            or body.get("content") is None:
            error_result["message"] = "NO DATA"
            return JsonResponse(error_result)
        else:
            to_username = body.get("to_username")
            from_username = body.get("from_username")
            content = body.get("content")
            try:
                if body.get("id") is None:
                    HrMessage.objects.create(
                        to_username=HrUser(username=to_username),
                        from_username=HrUser(username=from_username),
                        content=content
                    )
                else:
                    record = HrMessage.objects.get(body.get("id"))
                    record.content = body.get("content")
                    record.save()
                return JsonResponse(ok_result)
            except Exception as e:
                ex, ms, tb = sys.exc_info()
                error_result["message"] = format(ms)
                return JsonResponse(error_result)


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
                message_id = body.get("id")
                username = body.get("username")
                favorite = body.get("favorite")
                JST = timezone(timedelta(hours=+9), 'JST')
                now = datetime.now(JST)
                time_stamp = int(now.strftime('%s'))
                if favorite:
                    insert(message_id, username, time_stamp)
                else:
                    delete(message_id, username)
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
                message_id = body.get("id")
                all_nice = all_nice_query(message_id)
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


def insert(message_id, username, time_stamp):
    """いいねデータをDynamoDBにインサート"""
    table.put_item(
        Item={
            "message_id": message_id,
            "username": username,
            "created_at": time_stamp
        }
    )


def delete(message_id, username):
    """いいねデータをDynamoDBから削除"""
    table.delete_item(Key={'message_id': message_id, 'username': username})


def all_nice_query(message_id):
    """メッセージに対する全てのいいね！を取得"""
    data = table.query(
        KeyConditionExpression=Key('message_id').eq(message_id)
    )
    return data


def one_nice_query(message_id, username):
    """メッセージに対する一件のいいね！を取得"""
    data = table.query(
        KeyConditionExpression=Key('message_id').eq(message_id) & Key('username').eq(username)
    )
    return data