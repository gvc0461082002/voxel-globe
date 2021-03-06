from django.shortcuts import render
from django.http import HttpResponse

from voxel_globe.meta import models
from uuid import uuid4

# Create your views here.
def make_order_1(request):
  #Choose the image set

  image_set_list = models.ImageSet.objects.all()
  response = render(request, 'visualsfm/html/make_order_1.html', 
                {'image_set_list':image_set_list})
  return response

def make_order_2(request, image_set_id):
  #Choose the scene
  scene_list = models.Scene.objects.all()
  
  return render(request, 'visualsfm/html/make_order_2.html',
                {'scene_list':scene_list,
                 'image_set_id':image_set_id})

def make_order_3(request, image_set_id, scene_id):
  #MAKE the actual ORDER!
  from voxel_globe.visualsfm import tasks

  t = tasks.runVisualSfm.apply_async(args=(image_set_id, scene_id, True), user=request.user)

  #Crap ui filler   
  image_set = models.ImageSet.objects.get(id=image_set_id)
  image_list = image_set.images
  scene = models.Scene.objects.get(id=scene_id)
  
  #CALL THE CELERY TASK!
  response = render(request, 'visualsfm/html/make_order_3.html', 
                   {'origin':scene.origin,
                    'image_list':image_list, 'task_id':t.task_id})
  response.delete_cookie('visualsfm')
  
  return response
  
def order_status(request, task_id):
  import urllib2, json, os
  from celery.result import AsyncResult
  
  task = AsyncResult(task_id)
  status = {'task': task}
  
  if task.state == 'PROCESSING' and task.result['stage'] == 'generate match points':
    from vsi.iglob import glob
    status['mat'] = len(glob(os.path.join(task.result['processing_dir'], '*.mat'), False))
    status['sift'] = len(glob(os.path.join(task.result['processing_dir'], '*.sift'), False))
  
  return render(request, 'visualsfm/html/order_status.html',
                status)
  #return HttpResponse('Task %s\n%s' % (task_id, status))
