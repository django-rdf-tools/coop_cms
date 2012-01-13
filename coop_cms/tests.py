# -*- coding: utf-8 -*-

from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.template import Template, Context
from coop_cms.models import Link, NavNode, NavType, Document
import json
from django.core.exceptions import ValidationError
from coop_cms.settings import get_article_class
from model_mommy import mommy
from django.conf import settings
import os.path, shutil
from django.core.files import File

class NavigationTest(TestCase):

    def setUp(self):
        self.url_ct = ContentType.objects.get(app_label='coop_cms', model='link')
        NavType.objects.create(content_type=self.url_ct, search_field='url', label_rule=NavType.LABEL_USE_SEARCH_FIELD)
        self.editor = None
        self.staff = None
        self.srv_url = reverse("navigation_tree")

    def _log_as_editor(self):
        if not self.editor:
            self.editor = User.objects.create_user('toto', 'toto@toto.fr', 'toto')
            self.editor.is_staff = True
            can_edit_tree = Permission.objects.get(content_type__app_label='coop_cms', codename='change_navtree')
            self.editor.user_permissions.add(can_edit_tree)
            self.editor.save()
        
        self.client.login(username='toto', password='toto')
        
    def _log_as_staff(self):
        if not self.staff:
            self.staff = User.objects.create_user('titi', 'titi@titi.fr', 'titi')
            self.staff.is_staff = True
            self.staff.save()
        
        self.client.login(username='titi', password='titi')

    def test_view_in_admin(self):
        self._log_as_editor()
        url = reverse("admin:coop_cms_navtree_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
    def test_add_node(self):
        link = Link.objects.create(url="http://www.google.fr")
        self._log_as_editor()
        
        data = {
            'msg_id': 'add_navnode',
            'object_type':'coop_cms.link',
            'object_id': link.id,
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['label'], 'http://www.google.fr')
        
        nav_node = NavNode.objects.get(object_id=link.id, content_type=self.url_ct)
        self.assertEqual(nav_node.label, 'http://www.google.fr')
        self.assertEqual(nav_node.content_object, link)
        self.assertEqual(nav_node.parent, None)
        self.assertEqual(nav_node.ordering, 1)
        
        #Add a second node as child
        link2 = Link.objects.create(url="http://www.python.org")
        data['object_id'] = link2.id
        data['parent_id'] = link.id
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['label'], 'http://www.python.org')
        nav_node2 = NavNode.objects.get(object_id=link2.id, content_type=self.url_ct)
        self.assertEqual(nav_node2.label, 'http://www.python.org')
        self.assertEqual(nav_node2.content_object, link2)
        self.assertEqual(nav_node2.parent, nav_node)
        self.assertEqual(nav_node.ordering, 1)
        
    def test_add_node_twice(self):
        link = Link.objects.create(url="http://www.google.fr")
        self._log_as_editor()
        
        data = {
            'msg_id': 'add_navnode',
            'object_type':'coop_cms.link',
            'object_id': link.id,
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['label'], 'http://www.google.fr')
        
        nav_node = NavNode.objects.get(object_id=link.id, content_type=self.url_ct)
        self.assertEqual(nav_node.label, 'http://www.google.fr')
        self.assertEqual(nav_node.content_object, link)
        self.assertEqual(nav_node.parent, None)
        self.assertEqual(nav_node.ordering, 1)
        
        #Add a the same object a 2nd time
        data['object_id'] = link.id
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'error')
        
        nav_node = NavNode.objects.get(object_id=link.id, content_type=self.url_ct)
        self.assertEqual(nav_node.label, 'http://www.google.fr')
        self.assertEqual(nav_node.content_object, link)
        self.assertEqual(nav_node.parent, None)
        self.assertEqual(nav_node.ordering, 1)
        
    def test_move_node_to_parent(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(label=link.url, content_object=link, ordering=i+1, parent=None))
        
        self._log_as_editor()
        
        data = {
            'msg_id': 'move_navnode',
            'node_id': nodes[-2].id,
            'parent_id': nodes[0].id,
            'ref_pos': 'after',
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        
        node = NavNode.objects.get(id=nodes[-2].id)
        self.assertEqual(node.parent, nodes[0])
        self.assertEqual(node.ordering, 1)
        
        root_nodes = [node for node in NavNode.objects.filter(parent__isnull=True).order_by("ordering")]
        self.assertEqual(nodes[:-2]+nodes[-1:], root_nodes)
        self.assertEqual([1, 2, 3], [n.ordering for n in root_nodes])
        
    def test_move_node_to_root(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.toto.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(label=link.url, content_object=link, ordering=i+1, parent=None))
        nodes[1].parent = nodes[0]
        nodes[1].ordering = 1
        nodes[1].save()
        nodes[2].parent = nodes[0]
        nodes[2].ordering = 2
        nodes[2].save()
        
        self._log_as_editor()
        
        #Move after
        data = {
            'msg_id': 'move_navnode',
            'node_id': nodes[1].id,
            'ref_pos': 'after',
            'ref_id': nodes[0].id,            
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        
        node = NavNode.objects.get(id=nodes[1].id)
        self.assertEqual(node.parent, None)
        self.assertEqual(node.ordering, 2)
        self.assertEqual(NavNode.objects.get(id=nodes[0].id).ordering, 1)
        self.assertEqual(NavNode.objects.get(id=nodes[2].id).ordering, 1)
        
        #Move before
        data = {
            'msg_id': 'move_navnode',
            'node_id': nodes[2].id,
            'ref_pos': 'before',
            'ref_id': nodes[0].id,
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        #if result['status'] != 'success':
        #    print result['message']
        self.assertEqual(result['status'], 'success')
        
        node = NavNode.objects.get(id=nodes[2].id)
        self.assertEqual(node.parent, None)
        self.assertEqual(node.ordering, 1)
        self.assertEqual(NavNode.objects.get(id=nodes[0].id).ordering, 2)
        self.assertEqual(NavNode.objects.get(id=nodes[1].id).ordering, 3)
        
    def test_move_same_level(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(label=link.url, content_object=link, ordering=i+1, parent=None))
        
        self._log_as_editor()
        
        #Move the 4th just after the 1st one
        data = {
            'msg_id': 'move_navnode',
            'node_id': nodes[-2].id,
            'ref_id': nodes[0].id,
            'ref_pos': 'after',
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        
        nodes = [NavNode.objects.get(id=n.id) for n in nodes]#refresh
        [self.assertEqual(n.parent, None) for n in nodes]
        self.assertEqual([1, 3, 2, 4], [n.ordering for n in nodes])
        
        #Move the 1st before the 4th
        data = {
            'msg_id': 'move_navnode',
            'node_id': nodes[0].id,
            'ref_id': nodes[-1].id,
            'ref_pos': 'before',
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        
        nodes = [NavNode.objects.get(id=n.id) for n in nodes]#refresh
        [self.assertEqual(n.parent, None) for n in nodes]
        self.assertEqual([3, 2, 1, 4], [n.ordering for n in nodes])
        
    def test_delete_node(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(label=link.url, content_object=link, ordering=i+1, parent=None))
        
        self._log_as_editor()
        
        #remove the 2ns one
        data = {
            'msg_id': 'remove_navnode',
            'node_ids': nodes[1].id,
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
    
        nodes_after = NavNode.objects.all().order_by('ordering')
        self.assertEqual(3, len(nodes_after))
        self.assertTrue(nodes[1] not in nodes_after)
        for i, node in enumerate(nodes_after):
            self.assertTrue(node in nodes)
            self.assertTrue(i+1, node.ordering)
            
    def test_delete_node_and_children(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(label=link.url, content_object=link, ordering=i+1, parent=None))
        
        nodes[-1].parent = nodes[-2]
        nodes[-1].ordering = 1
        nodes[-1].save()
        
        self._log_as_editor()
        
        #remove the 2ns one
        data = {
            'msg_id': 'remove_navnode',
            'node_ids': nodes[-2].id,
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
    
        nodes_after = NavNode.objects.all().order_by('ordering')
        self.assertEqual(2, len(nodes_after))
        self.assertTrue(nodes[-1] not in nodes_after)
        self.assertTrue(nodes[-2] not in nodes_after)
        for i, node in enumerate(nodes_after):
            self.assertTrue(node in nodes)
            self.assertTrue(i+1, node.ordering)
            
    def test_rename_node(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(label=link.url, content_object=link, ordering=i+1, parent=None))
        
        self._log_as_editor()
        
        #rename the 1st one
        data = {
            'msg_id': 'rename_navnode',
            'node_id': nodes[0].id,
            'name': 'Google',
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
    
        node = NavNode.objects.get(id=nodes[0].id)
        self.assertEqual(data["name"], node.label)
        self.assertEqual(links[0].url, node.content_object.url)#object not renamed
        
        for n in nodes[1:]:
            node = NavNode.objects.get(id=n.id)
            self.assertEqual(n.label, node.label)
        
    def test_view_node(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        for i, link in enumerate(links):
            nodes.append(NavNode.objects.create(label=link.url, content_object=link, ordering=i+1, parent=None))
        
        self._log_as_editor()
        
        #remove the 2ns one
        data = {
            'msg_id': 'view_navnode',
            'node_id': nodes[0].id,
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['html'].find(nodes[0].get_absolute_url())>=0)
        self.assertTrue(result['html'].find(nodes[1].get_absolute_url())<0)
        self.assertTemplateUsed(response, 'coop_cms/navtree_content/default.html')
        
    def _do_test_get_suggest_list(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        self._log_as_editor()
        
        data = {
            'msg_id': 'get_suggest_list',
            'term': '.fr'
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['suggestions']), 3)
        
    def test_get_suggest_list(self):
        self._do_test_get_suggest_list()
        
    def test_get_suggest_list_get_label(self):
        
        nt = NavType.objects.get(content_type=self.url_ct)
        nt.search_field = ''
        nt.label_rule=NavType.LABEL_USE_GET_LABEL
        nt.save()
        self._do_test_get_suggest_list()
        
    def test_get_suggest_list_unicode(self):
        
        nt = NavType.objects.get(content_type=self.url_ct)
        nt.search_field = ''
        nt.label_rule=NavType.LABEL_USE_UNICODE
        nt.save()
        self._do_test_get_suggest_list()
        
    def test_get_suggest_list_only_not_in_navigation(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        link = links[0]
        node = NavNode.objects.create(label=link.url, content_object=link, ordering=1, parent=None)
        
        self._log_as_editor()
        
        data = {
            'msg_id': 'get_suggest_list',
            'term': '.fr'
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['suggestions']), 2)

        
    def test_unknow_message(self):
        self._log_as_editor()
        
        data = {
            'msg_id': 'oups',
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'error')
        
    def test_missing_message(self):
        self._log_as_editor()
        
        data = {
        }
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 404)
        
    def test_not_ajax(self):
        link = Link.objects.create(url="http://www.google.fr")
        self._log_as_editor()
        
        data = {
            'msg_id': 'add_navnode',
            'object_type':'coop_cms.link',
            'object_id': link.id,
        }
        
        response = self.client.post(self.srv_url, data=data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(0, NavNode.objects.count())
        
    def test_add_unknown_obj(self):
        self._log_as_editor()
        
        data = {
            'msg_id': 'add_navnode',
            'object_type':'coop_cms.link',
            'object_id': 11,
        }
        
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(0, NavNode.objects.count())
        
    def test_remove_unknown_node(self):
        self._log_as_editor()
        
        data = {
            'msg_id': 'remove_navnode',
            'node_ids': 11,
        }
        
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'error')
        
    def test_rename_unknown_node(self):
        self._log_as_editor()
        
        data = {
            'msg_id': 'remove_navnode',
            'node_id': 11,
            'label': 'oups'
        }
        
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'error')
        
    def test_check_auth(self):
        link = Link.objects.create(url='http://www.google.fr')
        
        for msg_id in ('add_navnode', 'move_navnode', 'rename_navnode', 'get_suggest_list', 'view_navnode', 'remove_navnode'):
            data = {
                'ref_pos': 'after',
                'name': 'oups',
                'term': 'goo',
                'object_type':'coop_cms.link',
                'object_id': link.id,
                'msg_id': msg_id
            }
            if msg_id != 'add_navnode':
                node = NavNode.objects.create(label=link.url, content_object=link, ordering=1, parent=None)
                data.update({'node_id': node.id, 'node_ids': node.id})
            
            self._log_as_staff()
            response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(response.status_code, 200)
            result = json.loads(response.content)
            self.assertEqual(result['status'], 'error')
            
            self._log_as_editor()
            response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(response.status_code, 200)
            result = json.loads(response.content)
            self.assertEqual(result['status'], 'success')
            
            NavNode.objects.all().delete()
            
    def test_set_out_of_nav(self):
        self._log_as_editor()
        
        link = Link.objects.create(url='http://www.google.fr')
        node = NavNode.objects.create(label=link.url, content_object=link, ordering=1, parent=None, in_navigation=True)
        
        data = {
            'msg_id': 'navnode_in_navigation',
            'node_id': node.id,
        }
        
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertNotEqual(result['message'], '')
        self.assertEqual(result['icon'], 'out_nav')
        node = NavNode.objects.get(id=node.id)
        self.assertFalse(node.in_navigation)
        
    def test_set_in_nav(self):
        self._log_as_editor()
        
        link = Link.objects.create(url='http://www.google.fr')
        node = NavNode.objects.create(label=link.url, content_object=link, ordering=1, parent=None, in_navigation=False)
        
        data = {
            'msg_id': 'navnode_in_navigation',
            'node_id': node.id,
        }
        
        response = self.client.post(self.srv_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result['status'], 'success')
        self.assertNotEqual(result['message'], '')
        self.assertEqual(result['icon'], 'in_nav')
        node = NavNode.objects.get(id=node.id)
        self.assertTrue(node.in_navigation)
        
    def test_delete_object(self):
        addrs = ("http://www.google.fr", "http://www.python.org", "http://www.quinode.fr", "http://www.apidev.fr")
        links = [Link.objects.create(url=a) for a in addrs]
        
        nodes = []
        parent = None
        for i, link in enumerate(links):
            parent = NavNode.objects.create(label=link.url, content_object=link, ordering=i+1, parent=parent)
            
        links[1].delete()
        
        self.assertEqual(0, Link.objects.filter(url=addrs[1]).count())
        for url in addrs[:1]+addrs[2:]:
            self.assertEqual(1, Link.objects.filter(url=url).count())
            
        nodes = NavNode.objects.all()
        self.assertEqual(1, nodes.count())
        node = nodes[0]
        self.assertEqual(addrs[0], node.content_object.url)

class NavigationParentTest(TestCase):
    
    def setUp(self):
        ct = ContentType.objects.get_for_model(get_article_class())
        NavType.objects.create(content_type=ct, search_field='title', label_rule=NavType.LABEL_USE_SEARCH_FIELD)
    
    def test_set_himself_as_parent_raise_error(self):
        art = get_article_class().objects.create(title='toto', content='oups')
        node = NavNode.objects.create(label=art.title, content_object=art, ordering=1, parent=None)
        self.assertRaises(ValidationError, art._set_navigation_parent, node.id)
        
    def test_set_child_as_parent_raise_error(self):
        art1 = get_article_class().objects.create(title='toto', content='oups')
        node1 = NavNode.objects.create(label=art1.title, content_object=art1, ordering=1, parent=None)
        
        art2 = get_article_class().objects.create(title='titi', content='oups')
        node2 = NavNode.objects.create(label=art2.title, content_object=art2, ordering=1, parent=node1)
        
        self.assertRaises(ValidationError, art1._set_navigation_parent, node2.id)
    
    def test_add_to_navigation_as_root(self):
        art1 = get_article_class().objects.create(title='toto', content='oups')
        art1.navigation_parent = 0
        ct = ContentType.objects.get_for_model(get_article_class())
        node = NavNode.objects.get(content_type=ct, object_id=art1.id)
        
    def test_add_to_navigation_as_child(self):
        art1 = get_article_class().objects.create(title='toto', content='oups')
        node1 = NavNode.objects.create(label=art1.title, content_object=art1, ordering=1, parent=None)
        art2 = get_article_class().objects.create(title='titi', content='oups')
        art2.navigation_parent = node1.id
        ct = ContentType.objects.get_for_model(get_article_class())
        node = NavNode.objects.get(content_type=ct, object_id=art2.id)
        self.assertEqual(node.parent.id, node1.id)
        
    def test_move_in_navigation_to_root(self):
        art1 = get_article_class().objects.create(title='toto', content='oups')
        node1 = NavNode.objects.create(label=art1.title, content_object=art1, ordering=1, parent=None)
        art2 = get_article_class().objects.create(title='titi', content='oups')
        node2 = NavNode.objects.create(label=art2.title, content_object=art2, ordering=1, parent=node1)
        art2.navigation_parent = 0
        ct = ContentType.objects.get_for_model(get_article_class())
        node = NavNode.objects.get(content_type=ct, object_id=art2.id)
        self.assertEqual(node.parent, None)
        
    def test_move_in_navigation_to_child(self):
        art1 = get_article_class().objects.create(title='toto', content='oups')
        node1 = NavNode.objects.create(label=art1.title, content_object=art1, ordering=1, parent=None)
        art2 = get_article_class().objects.create(title='titi', content='oups')
        node2 = NavNode.objects.create(label=art2.title, content_object=art2, ordering=1, parent=None)
        art2.navigation_parent = node1.id
        ct = ContentType.objects.get_for_model(get_article_class())
        node = NavNode.objects.get(content_type=ct, object_id=art2.id)
        self.assertEqual(node.parent.id, node1.id)
        
    def test_remove_from_navigation(self):
        art1 = get_article_class().objects.create(title='toto', content='oups')
        node1 = NavNode.objects.create(label=art1.title, content_object=art1, ordering=1, parent=None)
        art1.navigation_parent = None
        ct = ContentType.objects.get_for_model(get_article_class())
        self.assertRaises(NavNode.DoesNotExist, NavNode.objects.get, content_type=ct, object_id=art1.id)
        
    def test_get_navigation_parent(self):
        art1 = get_article_class().objects.create(title='toto', content='oups')
        node1 = NavNode.objects.create(label=art1.title, content_object=art1, ordering=1, parent=None)
        art2 = get_article_class().objects.create(title='titi', content='oups')
        node2 = NavNode.objects.create(label=art2.title, content_object=art2, ordering=1, parent=node1)
        art3 = get_article_class().objects.create(title='tutu', content='oups')
        self.assertEqual(art1.navigation_parent, 0)
        self.assertEqual(art2.navigation_parent, art1.id)
        self.assertEqual(art3.navigation_parent, None)
            
        
            
class TemplateTagsTest(TestCase):
    
    def setUp(self):
        link1 = Link.objects.create(url='http://www.google.fr')
        link2 = Link.objects.create(url='http://www.python.org')
        link3 = Link.objects.create(url='http://www.quinode.fr')
        link4 = Link.objects.create(url='http://www.apidev.fr')
        link5 = Link.objects.create(url='http://www.toto.fr')
        link6 = Link.objects.create(url='http://www.titi.fr')
        
        self.nodes = []
        
        self.nodes.append(NavNode.objects.create(label=link1.url, content_object=link1, ordering=1, parent=None))
        self.nodes.append(NavNode.objects.create(label=link2.url, content_object=link2, ordering=2, parent=None))
        self.nodes.append(NavNode.objects.create(label=link3.url, content_object=link3, ordering=3, parent=None))
        self.nodes.append(NavNode.objects.create(label=link4.url, content_object=link4, ordering=1, parent=self.nodes[2]))
        self.nodes.append(NavNode.objects.create(label=link5.url, content_object=link5, ordering=1, parent=self.nodes[3]))
        self.nodes.append(NavNode.objects.create(label=link6.url, content_object=link6, ordering=2, parent=self.nodes[3]))
        
    def test_view_navigation(self):
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul%}')
        html = tpl.render(Context({}))
        
        positions = [html.find('{0}'.format(n.content_object.url)) for n in self.nodes]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
        
    def _insert_new_node(self):
        link7 = Link.objects.create(url='http://www.tutu.fr')
        self.nodes.insert(-1, NavNode.objects.create(label=link7.url, content_object=link7, ordering=2, parent=self.nodes[3]))
        self.nodes[-1].ordering = 3
        self.nodes[-1].save()
        
    def test_view_navigation_order(self):
        self._insert_new_node()
        
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul%}')
        html = tpl.render(Context({}))
        
        positions = [html.find('{0}'.format(n.content_object.url)) for n in self.nodes]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
            
    def test_view_out_of_navigation(self):
        self.nodes[2].in_navigation = False
        self.nodes[2].save()
        
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul%}')
        html = tpl.render(Context({}))
        
        for n in self.nodes[:2]:
            self.assertTrue(html.find('{0}'.format(n.content_object.url))>=0)
            
        for n in self.nodes[2:]:
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)
            
    def test_view_navigation_custom_template(self):
        cst_tpl = Template('<span id="{{node.id}}">{{node.label}}</span>')
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul li_template=cst_tpl%}')
        
        html = tpl.render(Context({'cst_tpl': cst_tpl}))
        
        for n in self.nodes:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_navigation_custom_template_file(self):
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul li_template=coop_cms/test_li.html%}')
        
        html = tpl.render(Context({}))
        
        for n in self.nodes:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_navigation_css(self):
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul css_class=toto%}')
        html = tpl.render(Context({}))
        self.assertTrue(html.count('<li class="toto">'), len(self.nodes))
        
    def test_view_navigation_custom_template_and_css(self):
        tpl = Template(
            '{% load coop_navigation %}{%navigation_as_nested_ul li_template=coop_cms/test_li.html css_class=toto%}'
        )
        html = tpl.render(Context({}))
        self.assertTrue(html.count('<li class="toto">'), len(self.nodes))
            
        for n in self.nodes:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_breadcrumb(self):
        tpl = Template('{% load coop_navigation %}{% navigation_breadcrumb obj %}')
        html = tpl.render(Context({'obj': self.nodes[5].content_object}))
        
        for n in (self.nodes[2], self.nodes[3], self.nodes[5]) :
            self.assertTrue(html.find('{0}'.format(n.content_object.url))>=0)
            
        for n in (self.nodes[0], self.nodes[1], self.nodes[4]) :
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)
            
    def test_view_breadcrumb_out_of_navigation(self):
        for n in self.nodes:
            n.in_navigation = False
            n.save()
        
        tpl = Template('{% load coop_navigation %}{% navigation_breadcrumb obj %}')
        html = tpl.render(Context({'obj': self.nodes[5].content_object}))
        
        for n in (self.nodes[2], self.nodes[3], self.nodes[5]) :
            self.assertTrue(html.find('{0}'.format(n.content_object.url))>=0)
            
        for n in (self.nodes[0], self.nodes[1], self.nodes[4]) :
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)

    def test_view_breadcrumb_custom_template(self):
        cst_tpl = Template('<span id="{{node.id}}">{{node.label}}</span>')
        tpl = Template('{% load coop_navigation %}{% navigation_breadcrumb obj li_template=cst_tpl%}')
        
        html = tpl.render(Context({'obj': self.nodes[5].content_object, 'cst_tpl': cst_tpl}))
        
        for n in (self.nodes[2], self.nodes[3], self.nodes[5]) :
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_breadcrumb_custom_template_file(self):
        tpl = Template('{% load coop_navigation %}{% navigation_breadcrumb obj li_template=coop_cms/test_li.html%}')
        
        html = tpl.render(Context({'obj': self.nodes[5].content_object}))
        
        for n in (self.nodes[2], self.nodes[3], self.nodes[5]) :
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_children(self):
        tpl = Template('{% load coop_navigation %}{%navigation_children obj %}')
        html = tpl.render(Context({'obj': self.nodes[3].content_object}))
        
        for n in self.nodes[4:]:
            self.assertTrue(html.find(n.content_object.url)>=0)
            
        for n in self.nodes[:4]:
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)
            
    def test_view_children_out_of_navigation(self):
        self.nodes[1].in_navigation = False
        self.nodes[1].save()
        
        self.nodes[5].in_navigation = False
        self.nodes[5].save()
        
        tpl = Template('{% load coop_navigation %}{%navigation_children obj %}')
        html = tpl.render(Context({'obj': self.nodes[3].content_object}))
        
        for n in (self.nodes[4], ):
            self.assertTrue(html.find(n.content_object.url)>=0)
            
        for n in self.nodes[:4] + [self.nodes[5]]:
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)
            
    def test_view_children_custom_template(self):
        cst_tpl = Template('<span id="{{node.id}}">{{node.label}}</span>')
        tpl = Template('{% load coop_navigation %}{%navigation_children obj  li_template=cst_tpl %}')
        html = tpl.render(Context({'obj': self.nodes[3].content_object, 'cst_tpl': cst_tpl}))
        
        for n in self.nodes[4:]:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_children_custom_template_file(self):
        tpl = Template('{% load coop_navigation %}{%navigation_children obj li_template=coop_cms/test_li.html %}')
        html = tpl.render(Context({'obj': self.nodes[3].content_object}))
        
        for n in self.nodes[4:]:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_children_order(self):
        self._insert_new_node()
        nodes = self.nodes[3].get_children(in_navigation=True)
        tpl = Template('{% load coop_navigation %}{%navigation_children obj%}')
        html = tpl.render(Context({'obj': self.nodes[3].content_object}))
        positions = [html.find(n.content_object.url) for n in nodes]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
            
    def test_view_siblings(self):
        tpl = Template('{% load coop_navigation %}{% navigation_siblings obj %}')
        html = tpl.render(Context({'obj': self.nodes[0].content_object}))
        for n in self.nodes[:3]:
            self.assertTrue(html.find('{0}'.format(n.content_object.url))>=0)
            
        for n in self.nodes[3:]:
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)
    
    def test_view_siblings_order(self):
        self._insert_new_node()
        all_nodes = [n for n in self.nodes]
        nodes = all_nodes[-1].get_siblings(in_navigation=True)
        tpl = Template('{% load coop_navigation %}{%navigation_siblings obj%}')
        html = tpl.render(Context({'obj': all_nodes[-1].content_object}))
        positions = [html.find(n.content_object.url) for n in nodes]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
            
    def test_view_siblings_out_of_navigation(self):
        self.nodes[2].in_navigation = False
        self.nodes[2].save()
        
        self.nodes[5].in_navigation = False
        self.nodes[5].save()
        
        tpl = Template('{% load coop_navigation %}{% navigation_siblings obj %}')
        html = tpl.render(Context({'obj': self.nodes[0].content_object}))
        
        for n in self.nodes[:2]:
            self.assertTrue(html.find('{0}'.format(n.content_object.url))>=0)
            
        for n in self.nodes[2:]:
            self.assertFalse(html.find('{0}'.format(n.content_object.url))>=0)
    
    def test_view_siblings_custom_template(self):
        cst_tpl = Template('<span id="{{node.id}}">{{node.label}}</span>')
        tpl = Template('{% load coop_navigation %}{% navigation_siblings obj li_template=cst_tpl%}')
        html = tpl.render(Context({'obj': self.nodes[0].content_object, 'cst_tpl': cst_tpl}))
        
        for n in self.nodes[:3]:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_view_siblings_custom_template_file(self):
        tpl = Template('{% load coop_navigation %}{% navigation_siblings obj li_template=coop_cms/test_li.html%}')
        html = tpl.render(Context({'obj': self.nodes[0].content_object}))
        
        for n in self.nodes[:3]:
            self.assertTrue(html.find(u'<span id="{0.id}">{0.label}</span>'.format(n))>=0)
            self.assertFalse(html.find('<a href="{0}">{1}</a>'.format(n.content_object.url, n.label))>=0)
            
    def test_navigation_no_nodes(self):
        NavNode.objects.all().delete()
        tpl = Template('{% load coop_navigation %}{%navigation_as_nested_ul%}')
        html = tpl.render(Context({})).replace(' ', '')
        self.assertEqual(html, '')
            
    def test_breadcrumb_no_nodes(self):
        NavNode.objects.all().delete()
        link = Link.objects.get(url='http://www.python.org')
        tpl = Template('{% load coop_navigation %}{% navigation_breadcrumb obj %}')
        html = tpl.render(Context({'obj': link})).replace(' ', '')
        self.assertEqual(html, '')
            
    def test_children_no_nodes(self):
        NavNode.objects.all().delete()
        link = Link.objects.get(url='http://www.python.org')
        tpl = Template('{% load coop_navigation %}{%navigation_children obj %}')
        html = tpl.render(Context({'obj': link })).replace(' ', '')
        self.assertEqual(html, '')
            
    def test_siblings_no_nodes(self):
        NavNode.objects.all().delete()
        link = Link.objects.get(url='http://www.python.org')
        tpl = Template('{% load coop_navigation %}{% navigation_siblings obj %}')
        html = tpl.render(Context({'obj': link})).replace(' ', '')
        self.assertEqual(html, '')
        
class DownloadDocTest(TestCase):

    def _clean_files(self):
        dirs = (settings.DOCUMENT_FOLDER, settings.PRIVATE_DOCUMENT_FOLDER)
        for d in dirs:
            try:
                dir_name = '{0}/{1}'.format(settings.MEDIA_ROOT, d)
                shutil.rmtree(dir_name)
            except:
                pass
    
    def setUp(self):
        settings.DOCUMENT_FOLDER = '_unittest_docs'
        settings.PRIVATE_DOCUMENT_FOLDER = '_unittest_private_docs'
        self._clean_files()
        u = User.objects.create(username='toto')
        u.is_superuser = True
        u.set_password('toto')
        u.save()

    def tearDown(self):
        self._clean_files()
        
    def _get_file(self, file_name='unittest1.txt'):
        full_name = os.path.normpath(os.path.dirname(__file__) + '/fixtures/' + file_name)
        return open(full_name, 'rb')
    
    def test_upload_public_doc(self):
        data = {
            'doc': self._get_file(),
            'is_private': False,
            'descr': 'a test file',
        }
        self.assertTrue(self.client.login(username='toto', password='toto'))
        response = self.client.post(reverse('coop_cms_upload_doc'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'close_popup_and_media_slide')
        public_docs = Document.objects.filter(is_private=False)
        self.assertEquals(1, public_docs.count())
        self.assertEqual(public_docs[0].name, data['descr'])
        f = public_docs[0].file
        f.open('rb')
        self.assertEqual(f.read(), self._get_file().read())
        
    def test_upload_doc_missing_fields(self):
        data = {
            'is_private': False,
        }
        self.assertTrue(self.client.login(username='toto', password='toto'))
        response = self.client.post(reverse('coop_cms_upload_doc'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content, 'close_popup_and_media_slide')
        self.assertEquals(0, Document.objects.all().count())

    def test_upload_doc_anonymous_user(self):
        data = {
            'doc': self._get_file(),
            'is_private': False,
        }
        response = self.client.post(reverse('coop_cms_upload_doc'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content, 'close_popup_and_media_slide')
        self.assertEquals(0, Document.objects.all().count())
        redirect_url = response.redirect_chain[-1][0]
        login_url = reverse('django.contrib.auth.views.login')
        self.assertTrue(redirect_url.find(login_url)>0)

        
    def test_upload_private_doc(self):
        data = {
            'doc': self._get_file(),
            'is_private': True,
        }
        self.assertTrue(self.client.login(username='toto', password='toto'))
        response = self.client.post(reverse('coop_cms_upload_doc'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'close_popup_and_media_slide')
        private_docs = Document.objects.filter(is_private=True)
        self.assertEquals(1, private_docs.count())
        self.assertEqual(private_docs[0].name, 'unittest1')
        f = private_docs[0].file
        f.open('rb')
        self.assertEqual(f.read(), self._get_file().read())
    
    def test_view_docs(self):
        file1 = File(self._get_file())
        doc1 = mommy.make_one(Document, is_private=True, file=file1)
        file2 = File(self._get_file())
        doc2 = mommy.make_one(Document, is_private=False, file=file2)
        
        self.assertTrue(self.client.login(username='toto', password='toto'))
        response = self.client.get(reverse('coop_cms_media_documents'))
        self.assertEqual(response.status_code, 200)
        
        self.assertContains(response, reverse('coop_cms_download_doc', args=[doc1.id]))
        self.assertNotContains(response, doc1.file.url)
        self.assertNotContains(response, reverse('coop_cms_download_doc', args=[doc2.id]))
        self.assertContains(response, doc2.file.url)
        
    def test_view_docs_anonymous(self):
        response = self.client.get(reverse('coop_cms_media_documents'), follow=True)
        self.assertEqual(response.status_code, 200)
        redirect_url = response.redirect_chain[-1][0]
        login_url = reverse('django.contrib.auth.views.login')
        self.assertTrue(redirect_url.find(login_url)>0)
    
    def test_download_public(self):
        #create a public doc
        file = File(self._get_file())
        doc = mommy.make_one(Document, is_private=False, file=file)
        
        #check the url
        private_url = reverse('coop_cms_download_doc', args=[doc.id])
        self.assertNotEqual(doc.get_download_url(), private_url)
        
        #login and download
        self.assertTrue(self.client.login(username='toto', password='toto'))
        response = self.client.get(doc.get_download_url())
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.content, self._get_file().read())
        
        #logout and download
        self.client.logout()
        response = self.client.get(doc.get_download_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self._get_file().read())
        
    
    def test_download_private(self):
        #create a public doc
        file = File(self._get_file())
        doc = mommy.make_one(Document, is_private=True, file=file)
        
        #check the url
        private_url = reverse('coop_cms_download_doc', args=[doc.id])
        self.assertEqual(doc.get_download_url(), private_url)
        
        #login and download
        self.assertTrue(self.client.login(username='toto', password='toto'))
        response = self.client.get(doc.get_download_url())
        self.assertEqual(response.status_code, 200)
        self.assertEquals(response['Content-Disposition'], "attachment; filename=unittest1.txt")
        self.assertEquals(response['Content-Type'], "text/plain")
        self.assertEqual(response.content, self._get_file().read())
        
        #logout and download
        self.client.logout()
        response = self.client.get(doc.get_download_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        redirect_url = response.redirect_chain[-1][0]
        login_url = reverse('django.contrib.auth.views.login')
        self.assertTrue(redirect_url.find(login_url)>0)