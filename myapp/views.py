# # video_app/views.py
# from django.http import FileResponse
# import os

# def get_video(request):
#     path = 'C:\\Users\\AAO\\Videos\\123.mp4'
#     with open(path, 'rb') as file:
#         response = FileResponse(file, content_type='video/mp4')
#         return response

import asyncio
import base64
import json
from django.http import FileResponse, StreamingHttpResponse, JsonResponse
from django.shortcuts import HttpResponse
import os
import uuid

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from myapp import consumers
from myapp.consumers import add_new_episode, delete_episode
from django.views.decorators.csrf import csrf_exempt





special_files_id = consumers.special_files_id
special_files = consumers.special_files

anime_episode_list_id = consumers.anime_episode_list_id
anime_episode_list = consumers.anime_episode_list


async def send(headers):

    channel_name = consumers.names

    channel_layer = get_channel_layer()
    await channel_layer.send(
        channel_name,
        {
            'type': 'chat_message',
            
            'message': json.dumps(headers)
        }
    )

async def get_video(request):
    # 获取范围请求头
    range_header = request.headers.get('Range', None)

    title = request.GET.get('title')
    episode_title = request.GET.get('episode_title')
        
    # 如果存在范围请求头，则解析范围
    if range_header:
        print(f'等待range资源{range_header}')
        file_size, start_range, end_range, content_length, chunk = await get_video_from_client_with_range(range_header,title,episode_title)
        print(f'获得range资源{range_header}')
        # content_length = end_range - start_range + 1
        content_range = f'bytes {start_range}-{end_range}/{file_size}'

        response = HttpResponse(content=chunk, content_type='video/MKV', status=206)
        # response['Content-Disposition'] = f'inline; filename=123.mp4'
        response['Content-Length'] = content_length
        response['Content-Range'] = content_range

    return response
async def get_video_from_client_with_range(range,title,episode):

    UUID = str(uuid.uuid4())
    data = {'UUID':UUID,'Range':range,'Title':title, 'Episode':episode}
    # await .send(json.dump({'Type': 'file','FileType': 'video','UUID':UUID, 'Data': data}))
    await send({'Type': 'file','FileType': 'video','UUID':UUID, 'Data': data})

    consumers.add_new_special_file(UUID)
    
    index = consumers.special_files_id.index(UUID)
    data = consumers.special_files[index]['Data']
    # print(2)
    while not data:
        await asyncio.sleep(0.1)
        index = consumers.special_files_id.index(UUID)
        data = consumers.special_files[index]['Data']
    consumers.delete_special_files(UUID)
    # print(data)
    data = data[0]
    # print(data['file_size'])
    file_size = data['file_size']
    start = data['start'] 
    end= data['end']
    content_length = data['content_length']
    chunk = data['chunk']
    chunk = chunk.encode(encoding='utf-8')
    # b64解码,获得原二进制序列
    chunk = base64.b64decode(chunk)
    return file_size, start, end, content_length, chunk

async def get_next_chunk_by_id(UUID):

    index = special_files_id.index(UUID)
    chunks = special_files[index]['Data']

    while True:
        if chunks:
            break
        await asyncio.sleep(0.1)
        index = special_files_id.index(UUID)
        chunks = special_files[index]['Data']

    current_chunk = chunks[0]
    chunks.pop(0)
    return current_chunk

async def file_stream(UUID):
    while True:
        current_chunk = await get_next_chunk_by_id(UUID)
        chunk_data = current_chunk['Chunk']
        # 将字符串重新编码为utf-8的二进制序列（该序列被b64编码过）
        chunk_data = chunk_data.encode(encoding='utf-8')
        # b64解码,获得原二进制序列
        chunk_data = base64.b64decode(chunk_data)


        yield chunk_data
        if current_chunk['Is_the_last'] == True:
            consumers.delete_special_files(UUID)
            break
  
async def get_anime_cover(request):
    print (f'special_files_len{len(special_files)}')
    print('get_anime_cover ---- start')
    title = request.GET.get('title')

    UUID = str(uuid.uuid4())
    headers = {
        'Type': 'file',
        'Title': title,
        'UUID': UUID,
        'FileType': 'cover'
    }
    consumers.add_new_special_file(UUID)
    await send(headers)
    print('get_anime_cover ---- over')
    return StreamingHttpResponse(file_stream(UUID),content_type='application/octet-stream')

async def get_anime_info(request):
    
    
    print('get_anime_info')
    await send({'Type': 'animeinfo'})
    
    anime_titles = consumers.anime_titles
    while not anime_titles:
        await asyncio.sleep(1)
        anime_titles = consumers.anime_titles
    
    msg = {'titles': anime_titles}
    anime_titles = []
    # print(msg)
    print('get_anime_info_over')
    # print(msg)
    return JsonResponse(msg)

# # 通过文件的UUID（自定义的UUID）为文件缓冲区添加新文件
# def add_new_episode(UUID):
#     global anime_episode_list_id
#     global anime_episode_list
#     anime_episode_list_id.append(UUID)
#     anime_episode_list.append({'UUID': UUID, 'episode_title_list': []})
#     pass

# # 根据文件UUID删除文件缓冲区的文件
# def delete_episode(UUID):
#     global anime_episode_list_id
#     global anime_episode_list
#     index = anime_episode_list_id.index(UUID)
#     anime_episode_list_id.pop(index)
#     anime_episode_list.pop(index)

@csrf_exempt
async def get_current_anime_episode_titles(request):
    print('get_current_anime_episode_titles_start')
    json_data = json.loads(request.body)
    # anime_title = request.POST.get('anime_title')
    # print(request.GET)
    anime_title = json_data.get('anime_title')
    # print(anime_title)
    UUID = str(uuid.uuid4())
    msg = {
        'Type': 'episode_titles',
        'Title': anime_title,
        'UUID': UUID,
    }
    # print(msg)
    await send(msg)
    # global anime_episode_list_id
    # global anime_episode_list
    add_new_episode(UUID)
    # print(anime_episode_list_id)
    index = anime_episode_list_id.index(UUID)
    episode_title_list = anime_episode_list[index]['episode_title_list']
    while(not episode_title_list):
        await asyncio.sleep(0.1)
        index = anime_episode_list_id.index(UUID)
        episode_title_list = anime_episode_list[index]['episode_title_list']
    delete_episode(UUID)
    # print(episode_title_list)
    print('get_current_anime_episode_titles_over')
    # JsonResponse(msg)
    return JsonResponse({'episode_title_list':episode_title_list})