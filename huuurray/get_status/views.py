from django.http.response import JsonResponse


def send_status(request):
    ok_result = {"statusCode": "200"}
    return JsonResponse(ok_result)
