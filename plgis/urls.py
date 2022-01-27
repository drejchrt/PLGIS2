from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('lookup/<string>', views.lookup, name='lookup'),
    path('constructor', views.constructor, name='constructor'),

    path('circuits', views.list, name='circuits'),  # list
    path('circuits/<int:id>', views.detail, name='circuit'),  # detail
    path('circuits/<int:id>/edit', views.edit, name='circuit_edit'),  # edit
    path('circuits/<int:id>/delete', views.delete, name='circuit_delete'),  # delete
    path('circuits/new', views.new, name='circuit_new'),  # new

    path('towers', views.list, name='towers'),  # list
    path('towers/<int:id>', views.detail, name='tower'),  # detail
    path('towers/<int:id>/edit', views.edit, name='tower_edit'),  # edit
    path('towers/<int:id>/delete', views.delete, name='tower_delete'),  # delete
    path('towers/new', views.new, name='tower_new'),  # new

    path('users/new', views.request_new_account, name='register'),
    path('users/<int:id>', views.user_profile, name='user'),

    path('img_upload',views.img_upload, name='img_upload'),
    path('img_list',views.img_list, name='img_list'),

    path('inspection/', views.inspection, name='inspection'),
    path('inspection/<int:circuit_id>', views.inspection, name='inspection'),
    path('inspection/<int:circuit_id>/<str:section_id>', views.inspection, name='inspection'),
    path('inspection/<int:circuit_id>/<str:section_id>/<int:image_id>', views.inspection, name='inspection'),

    path('marking/<int:mark_id>', views.marking, name='marking'),

    path('fault/<int:fault_id>', views.fault, name='fault'),
    path('fault/<int:fault_id>/delete', views.fault, name='fault_delete'), # redirect to delete view
    path('fault/<int:fault_id>/edit', views.fault, name='fault_edit'), # redirect to delete view
]


