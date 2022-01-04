from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('users/new', views.request_new_account, name='register'),
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

    path('spanfields', views.list, name='spanfields'),  # list
    path('spanfields/<int:id>', views.detail, name='spanfield'),  # detail
    path('spanfields/<int:id>/edit', views.edit, name='spanfield_edit'),  # edit
    path('spanfields/<int:id>/delete', views.delete, name='spanfield_delete'),  # delete
    path('spanfields/new', views.new, name='spanfield_new'),  # new

    path('components', views.list, name='components'),  # list
    path('components/<int:id>', views.detail, name='component'),  # detail
    path('components/<int:id>/edit', views.edit, name='component_edit'),  # edit
    path('components/<int:id>/delete', views.delete, name='component_delete'),  # delete
    path('components/new', views.new, name='component_new'),  # new
]
