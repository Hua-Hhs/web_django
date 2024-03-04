# myapp/consumers.py

from channels.generic.websocket import AsyncWebsocketConsumer
import json
import uuid
import asyncio
import base64

names = ''

special_files = []
special_files_id = []
current_special_files_info = {'is_used': True}

anime_episode_list = []
anime_episode_list_id = []
consumers = []

anime_titles = []

anime_covers = []


current_path = ''

# 通过文件的UUID（自定义的UUID）为文件缓冲区添加新文件
def add_new_episode(UUID):
    global anime_episode_list_id
    global anime_episode_list
    anime_episode_list_id.append(UUID)
    anime_episode_list.append({'UUID': UUID, 'episode_title_list': []})
    pass

# 根据文件UUID删除文件缓冲区的文件
def delete_episode(UUID):
    global anime_episode_list_id
    global anime_episode_list
    index = anime_episode_list_id.index(UUID)
    anime_episode_list_id.pop(index)
    anime_episode_list.pop(index)

# 通过文件的UUID（自定义的UUID）为文件缓冲区添加新文件
def add_new_special_file(UUID):
    global special_files_id
    global special_files
    special_files_id.append(UUID)
    special_files.append({'UUID': UUID, 'Data': []})
    pass

# 根据文件UUID删除文件缓冲区的文件
def delete_special_files(UUID):
    global special_files_id
    global special_files
    index = special_files_id.index(UUID)
    special_files.pop(index)
    special_files_id.pop(index)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        global names
        names = self.channel_name

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        # print('channel_name:'+self.channel_name)
        pass
        # await self.channel_layer.send(
        #     self.channel_name,
        #     {
        #         'type': 'chat_message',
        #         'message': "123123"
        #     }
        # )

        msg = json.loads(text_data)
        try:
            # 客户端发送文件头报文用于识别不同文件或同一文件的多次同时请求时分别记录不同进度
            # 发送的报文类型为文件头报文，获取报文的UUID，在文件缓冲区创建文件，用于接收发来的文件,herder从
            if (msg['Type'] == 'header'):
                pass
                # UUID = msg['UUID']
                # add_new_special_file(UUID)
            # 接收文件
            elif (msg['Type'] == 'file'):
                UUID = msg['UUID']
                data = msg['Data']
                global special_files_id
                global special_files
                index = special_files_id.index(UUID)
                special_files[index]['Data'].append(data)
                # data = {'Chunk' : chunk, 'Is_the_last' : False}
            # 接收文件夹信息
            elif (msg['Type'] == 'folder'):
                global current_special_files_info
                # print(msg)
                current_special_files_info = msg['Infos']
                # current_special_files_info.append({'is_used'L})
            elif (msg['Type'] == 'episode_titles'):
                UUID = msg['UUID']
                episode_title_list = msg['episode_title_list']
                global anime_episode_list_id
                global anime_episode_list
                index = anime_episode_list_id.index(UUID)
                anime_episode_list[index]['episode_title_list'] = episode_title_list
            elif (msg['Type'] == 'title'):
                global anime_titles 
                anime_titles = msg['titles']
            

        except Exception as e:
            print(f"download special file error: {e} ")

    async def chat_message(self, event):
        message = event['message']
        await self.send(text_data=message)

