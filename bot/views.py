from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
# Create your views here.

from linebot import LineBotApi, WebhookHandler, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextSendMessage, ImageSendMessage
import requests
from bs4 import BeautifulSoup

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
parse = WebhookParser(settings.LINE_CHANNEL_SECRET)


def get_invoice_new():
    data = ''
    try:
        content = requests.get('http://invoice.etax.nat.gov.tw/invoice.xml')
        tree = ET.fromstring(content.text)  # 解析XML
        items = list(tree.iter(tag='item'))  # 取得item標籤內容
        title = items[0][0].text  # 期別
        ptext = items[0][3].text  # 中獎號碼
        ptext = ptext.replace('<p>', '').replace('</p>', '\n')
        data += title + '\n' + ptext[:-1]  # ptext[:-1]為移除最後一個\n
        return data
    except Exception as e:
        print(e)


def get_invoice_old():
    try:
        content = requests.get('http://invoice.etax.nat.gov.tw/invoice.xml')
        tree = ET.fromstring(content.text)  # 解析XML
        items = list(tree.iter(tag='item'))  # 取得item標籤內容
        message = ''
        for i in range(1, 2):
            title = items[i][0].text  # 期別
            ptext = items[i][3].text  # 中獎號碼
            ptext = ptext.replace('<p>', '').replace('</p>', '\n')
            message = message + title + '\n' + ptext + '\n'
        message = message[:-2]
        return message
    except Exception as e:
        print(e)


def show3digit(text):
    try:
        content = requests.get('http://invoice.etax.nat.gov.tw/invoice.xml')
        tree = ET.fromstring(content.text)
        items = list(tree.iter(tag='item'))  # 取得item標籤內容
        ptext = items[0][3].text  # 中獎號碼
        ptext = ptext.replace('<p>', '').replace('</p>', '')
        temlist = ptext.split('：')
        prizelist = []  # 特別獎或特獎後三碼
        prizelist.append(temlist[1][5:8])
        prizelist.append(temlist[2][5:8])
        prize6list1 = []  # 頭獎後三碼六獎中獎號碼
        for i in range(3):
            prize6list1.append(temlist[3][9*i+5:9*i+8])
        if text in prizelist:
            message = '符合特別獎或特獎後三碼，請繼續輸入發票前五碼！'
        elif text in prize6list1:
            message = '恭喜！至少中二百元，請繼續輸入發票前五碼！'
        else:
            message = '很可惜，未中獎。請輸入下一張發票最後三碼。'
        return message
    except Exception as e:
        print(e)


def show5digit(text):
    try:
        content = requests.get('http://invoice.etax.nat.gov.tw/invoice.xml')
        tree = ET.fromstring(content.text)
        items = list(tree.iter(tag='item'))  # 取得item標籤內容
        ptext = items[0][3].text  # 中獎號碼
        ptext = ptext.replace('<p>', '').replace('</p>', '')
        temlist = ptext.split('：')
        special1 = temlist[1][0:5]
        special2 = temlist[2][0:5]
        special3 = temlist[3]
        special4 = temlist[3][1:5]
        special5 = temlist[3][10:14]
        special6 = temlist[3][19:23]
        #prizehead = []
        # for i in range(3):
        # prizehead.append(temlist[3][9*i:9*i+5])

        if text in special1:
            message = '恭喜！此張發票中了特別獎！'
        elif text in special2:
            message = '恭喜！此張發票中了特獎！'

        elif text in special3:
            message = '恭喜！此張發票中了頭獎！'
            if text in special4:
                message = '恭喜！此張發票中了二獎！'
            return message
        else:
            message = '很可惜，未中獎。請輸入下一張發票最後三碼。'
        return message
    except Exception as e:
        print(e)


@csrf_exempt
def callback(request):
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')
        try:
            events = parse.parse(body, signature)
        except InvalidSignatureError:
            return HttpResponseForbidden()
        except LineBotApiError:
            return HttpResponseBadRequest()
        for event in events:
            if isinstance(event, MessageEvent):
                text = event.message.text
                message = None
                print(text)
                if text == '1':
                    message = '早安'
                elif text == '2':
                    message = '午安'
                elif text == '3':
                    message = '晚安'
                elif '早安' in text:
                    message = '早安你好!'
                elif '捷運' in text:
                    mrts = {
                        '台北': 'https://web.metro.taipei/pages/assets/images/routemap2023n.png',
                        '台中': 'https://assets.piliapp.com/s3pxy/mrt_taiwan/taichung/20201112_zh.png?v=2',
                        '高雄': 'https://upload.wikimedia.org/wikipedia/commons/5/56/%E9%AB%98%E9%9B%84%E6%8D%B7%E9%81%8B%E8%B7%AF%E7%B6%B2%E5%9C%96_%282020%29.png'
                    }
                    image_url = 'https://web.metro.taipei/pages/assets/images/routemap2023n.png'
                    for mrt in mrts:
                        if mrt in text:
                            image_url = mrts[mrt]
                            print(image_url)
                            break

                elif '本期號碼' in text:
                    message = get_invoice_new()
                elif '前期號碼' in text:
                    message = get_invoice_old()
                elif '後三碼' in text:
                    message = '請輸入發票最後三碼進行對獎！'
                elif len(text) == 3:
                    message = show3digit(text)
                elif len(text) == 5:
                    message = show5digit(text)

                else:
                    message = '抱歉，我不知道你說甚麼?'

                if message is None:
                    message_obj = ImageSendMessage(image_url, image_url)
                else:
                    message_obj = TextSendMessage(text=message)

                line_bot_api.reply_message(event.reply_token, message_obj)
        return HttpResponse()
    else:
        return HttpResponseBadRequest()

# Create your views here.


def index(request):
    return HttpResponse("Line bot!")
