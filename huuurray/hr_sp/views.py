import traceback,sys
import json
import datetime
from datetime import datetime, timedelta, timezone
import boto3
from boto3.dynamodb.conditions import Key, Attr
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from huuurray.hr_sp.models import ToPointDay, FromPointDay
from huuurray.hr_user.models import HrUser, FavoriteUser
from huuurray.post_data.views import exec_query


# 変数定義
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
table = dynamodb.Table('Huuurray_Dev_Point')


@csrf_exempt
def get_point(request):
    """ポイントデータの取得"""
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
            or body.get("send_sp_to") is None:
            error_result["message"] = "NO DATA"
            return JsonResponse(error_result)
        else:
            to_username = body.get("to_username")
            from_username = body.get("from_username")
            send_sp_to = body.get("send_sp_to")

            try:
                # もらったポイントについての集計
                sp_sql = """
                    SELECT
                        sum(point) as sp
                    FROM
                        hr_sp_topointday
                    WHERE
                        username_id = \"%s\" ;
                """
                to_sp_obj = exec_query(sp_sql % to_username)
                to_sp_dist = list(to_sp_obj)
                if  to_sp_dist[0]["sp"] is None:
                    ok_result["sp"] = 0
                else:
                    ok_result["sp"] = int(to_sp_dist[0]["sp"])

                # 送ったポイントについての集計
                from_sp_sql = """
                    SELECT
                        sum(point) as sp
                    FROM
                        hr_sp_frompointday
                    WHERE
                        username_id = \"%s\" ;
                """
                from_sp_obj = exec_query(from_sp_sql % to_username)
                from_sp_dist = list(from_sp_obj)
                if  from_sp_dist[0]["sp"] is None:
                    ok_result["send_sp"] = 0
                else:
                    ok_result["send_sp"] = int(from_sp_dist[0]["sp"])

                # 対象ユーザーへ送ったポイントが0の場合のみDynamoDBから取得
                if send_sp_to == 0:
                    send_sp_to = send_to_query(to_username, from_username)
                    send_sp_to_sum = 0
                    for record in send_sp_to["Items"]:
                        send_sp_to_sum += record["point"]
                    ok_result["send_sp_to"] = send_sp_to_sum
                else:
                    ok_result["send_sp_to"] = send_sp_to

                # お気に入り登録者数の取得
                favorite_cnt = FavoriteUser.objects.filter(
                    to_username=HrUser(username=to_username)
                ).exclude(delete_flg="1").count()
                ok_result["favorite"] = favorite_cnt

                # お気に入り登録数の取得
                favorite_to_cnt = FavoriteUser.objects.filter(
                    from_username=HrUser(username=to_username)
                ).exclude(delete_flg="1").count()
                ok_result["favorite_to"] = favorite_to_cnt

                ok_result["to_username"] = to_username
                ok_result["from_username"] = from_username
                return JsonResponse(ok_result)
            except:
                ex, ms, tb = sys.exc_info()
                error_result["message"] = format(ms)
                return JsonResponse(error_result)


@csrf_exempt
def upsert(request):
    """ポイントデータの新規作成"""
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
            or body.get("point") is None \
            or body.get("type") is None:
            error_result["message"] = "NO DATA"
            return JsonResponse(error_result)
        else:
            to_username = body.get("to_username")
            from_username = body.get("from_username")
            point = body.get("point")
            ptype = body.get("type")
            JST = timezone(timedelta(hours=+9), 'JST')
            now = datetime.now(JST)
            time_stamp = int(now.strftime('%s'))
            today = datetime(
                now.year,
                now.month,
                now.day,
                0, 0, 0, 0)
            today_s = int(today.strftime('%s'))
            today_yymmdd = today.strftime('%Y-%m-%d')
            try:
                # DynamoDBにインサート
                insert(
                    to_username,
                    from_username,
                    point,
                    ptype,
                    time_stamp
                )

                # 本日のもらったポイントについての集計
                today_data = today_to_query(to_username, today_s)
                #ok_result["data"] = today_data
                to_point_sum = 0
                for record in today_data["Items"]:
                    to_point_sum += record["point"]
                data = {
                    "username": HrUser(username=to_username),
                    "date": today_yymmdd,
                    "point": to_point_sum,
                    "delete_flg": "0"
                }
                ToPointDay.objects.update_or_create(
                    username=HrUser(username=to_username),
                    date=today_yymmdd,
                    defaults=data
                )

                # 本日の送ったポイントについての集計
                today_data = today_from_query(from_username, today_s)
                from_point_sum = 0
                for record in today_data["Items"]:
                    from_point_sum += record["point"]
                data = {
                    "username": HrUser(username=from_username),
                    "date": today_yymmdd,
                    "point": from_point_sum,
                    "delete_flg": "0"
                }
                FromPointDay.objects.update_or_create(
                    username=HrUser(username=from_username),
                    date=today_yymmdd,
                    defaults=data
                )

                return JsonResponse(ok_result)
            except:
                ex, ms, tb = sys.exc_info()
                error_result["message"] = format(ms)
                return JsonResponse(error_result)


def insert(to_username, from_username, point, ptype, time_stamp):
    """ポイントデータをDynamoDBにインサート"""
    table.put_item(
        Item={
            "to_username": to_username,
            "from_username": from_username,
            "point": point,
            "type": ptype,
            "created_at": time_stamp
        }
    )


def today_to_query(to_username, today):
    """今日のもらったポイントデータをDynamoDBから取得"""
    data = table.query(
        KeyConditionExpression=Key('to_username').eq(to_username) & Key('created_at').gte(today)
    )
    return data


def today_from_query(from_username, today):
    """今日の送ったポイントデータをDynamoDBから取得"""
    data = table.query(
        IndexName="from_username-created_at-index",
        KeyConditionExpression=Key('from_username').eq(from_username) & Key('created_at').gte(today)
    )
    return data


def send_to_query(to_username, from_username):
    """from,toユーザーから送ったポイントをDynamoDBから取得"""
    data = table.query(
        IndexName="to_username-from_username-index",
        KeyConditionExpression=Key('to_username').eq(to_username) & Key('from_username').eq(from_username)
    )
    return data
