import os
from os import environ as env

from django.shortcuts import render, redirect, HttpResponse
from django.core import serializers

import voxel_globe.download.forms as forms

from .tools import xfilesend_response

# Create your views here.
def index(request):
  return render(request, 'download/html/index.html',
                {'title': 'Voxel Globe - Download',
                 'page_title': 'Download'})

def tiepoint(request):
  if request.method == 'POST':

    form = forms.TiePointForm(request.POST)

    if form.is_valid():
      image_set = form.cleaned_data['image_set']
      all_tiepoints = []
      for image in image_set.images.all():
        tiepoints = image.tiepoint_set.all()
        for tiepoint in tiepoints:
          all_tiepoints.append(tiepoint)
      response =  HttpResponse(serializers.serialize('geojson', all_tiepoints))
      response['Content-Disposition'] = 'attachment; ' + \
          'filename=tie_points_%d.json' % image_set.id
      response['Content-Length'] = len(response.content)
      return response
  else:
    form = forms.TiePointForm()

  return render(request, 'main/form.html',
                {'form':form,
                 'action': '/download/tiepoint'})

def control_point(request):
  if request.method == 'POST':

    form = forms.TiePointForm(request.POST)

    if form.is_valid():
      image_set = form.cleaned_data['image_set']
      control_points = []
      for image in image_set.images.all():
        tiepoints = image.tiepoint_set.all()
        for tiepoint in tiepoints:
          if tiepoint.control_point not in control_points:
            control_points.append(tiepoint.control_point)
      response = HttpResponse(serializers.serialize('geojson', control_points))
      response['Content-Disposition'] = 'attachment; ' + \
          'filename=control_points_%d.json' % image_set.id
      response['Content-Length'] = len(response.content)
      return response
  else:
    form = forms.TiePointForm()

  return render(request, 'main/form.html',
                {'form':form,
                 'action': '/download/control_point'})

def point_cloud_ply(request):
  if request.method == 'POST':
    form = forms.PointCloudForm(request.POST)
    if form.is_valid():
      point_cloud = form.cleaned_data['point_cloud']

      return xfilesend_response(request, 
          env['VIP_NGINX_XSENDFILE_PREFIX']+point_cloud.filename_path,
          download_name='point_cloud_%d.ply' % point_cloud.id)
  else:
    form = forms.PointCloudForm()

  return render(request, 'main/form.html',
                {'form':form,
                 'action': '/download/point_cloud'})

def cameras_krt(request):
  if request.method == 'POST':
    form = forms.CameraForm(request.POST)
    if form.is_valid():
      from StringIO import StringIO
      import math
      import json
      import zipfile

      import numpy as np

      from voxel_globe.tools.camera import get_krt

      image_set = form.cleaned_data['image_set']
      camera_set = form.data['camera_set']

      _,_,_,origin = get_krt(image_set.images.all()[0], camera_set)
      krts = []
      name_format = 'frame_%%0%dd.txt' % int(math.ceil(math.log10(max(image_set.images.all().values_list('id', flat=True)))))
      zip_s = StringIO()
      with zipfile.ZipFile(zip_s, 'w', zipfile.ZIP_DEFLATED) as zipper:
        for image in image_set.images.all():
          k,r,t,_ = get_krt(image, camera_set, origin=origin)
          krt_s = StringIO()
          np.savetxt(krt_s, np.array(k))
          krt_s.write('\n')
          np.savetxt(krt_s, np.array(r))
          krt_s.write('\n')
          np.savetxt(krt_s, np.array(t).T)
          zipper.writestr(name_format % image.id, krt_s.getvalue())
        zipper.writestr('scene.json', json.dumps({'origin':origin, 'longitude':origin[0], 'latitude':origin[1], 'altitude':origin[2]}))

      response = HttpResponse(zip_s.getvalue(), content_type='application/zip')
      response['Content-Length'] = len(response.content)
      response['Content-Disposition'] = 'attachment; ' + \
          'filename=cameras_%d.zip' % image_set.id
      return response

  else:
    form = forms.CameraForm()

  return render(request, 'main/form.html',
                {'form':form,
                 'action': '/download/cameras'})

def image(request):
  if request.method == 'POST':
    form = forms.ImageForm(request.POST)
    if form.is_valid():
      image = form.cleaned_data['image']
      filename = image.filename_path
      return xfilesend_response(request, 
          env['VIP_NGINX_XSENDFILE_PREFIX']+filename,
          download_name=os.path.basename(filename))
  else:
    form = forms.ImageForm()
  return render(request, 'main/form.html',
                {'form':form,
                 'action': '/download/image'})