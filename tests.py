import unittest
import getpass
from pysb import SbSession
from os import listdir
from os.path import isfile, join
from six.moves import input

class TestPysbMethods(unittest.TestCase):
    SB_CATALOG_ITEM_ID = '4f4e4760e4b07f02db47df9c'
    BETA_TEST_COMMUNITY_ID = '54d518d8e4b0afcce73d1a65'
    TEST_USER = None
    TEST_PASSWORD = None

    @classmethod
    def setUpClass(cls):
        super(TestPysbMethods, cls).setUpClass()

        cls.TEST_USER = input("Username:  ")
        cls.TEST_PASSWORD = getpass.getpass()

    def test_get_item(self):
        sb = SbSession('beta').login(self.TEST_USER, self.TEST_PASSWORD)
        item = sb.get_item(self.SB_CATALOG_ITEM_ID)
        self.assertTrue(item is not None)
        self.assertEqual(item['title'], 'ScienceBase Catalog')

    def test_ancestors_field_in_find_items(self):
        sb = SbSession('beta').login(self.TEST_USER, self.TEST_PASSWORD)
        itemsJson = sb.find_items({'parentId':self.BETA_TEST_COMMUNITY_ID, 'fields':'parentId,ancestors'})
        self.assertTrue(itemsJson['items'] is not None)
        self.assertTrue(isinstance(itemsJson['items'], list))
        self.assertTrue(len(itemsJson['items']) > 0)
        item = itemsJson['items'][0]
        self.assertTrue(isinstance(item['ancestors'], list))
        self.assertTrue(item['parentId'] is not None)
        self.assertTrue(item['parentId'] in item['ancestors'])

    def test_ancestors_field_in_get_item(self):
        sb = SbSession('beta').login(self.TEST_USER, self.TEST_PASSWORD)
        item = sb.get_item(self.BETA_TEST_COMMUNITY_ID, {'fields':'parentId,ancestors'})
        self.assertTrue(isinstance(item['ancestors'], list))
        self.assertTrue(item['parentId'] is not None)
        self.assertTrue(item['parentId'] in item['ancestors'])

    def test_upload_shapefile_no_scrape(self):
        sb = SbSession('beta').login(self.TEST_USER, self.TEST_PASSWORD)
        file_dir = 'test/data/FHP_Great_Lakes_Basin_boundary'
        files = ["%s/%s" % (file_dir, f) for f in listdir(file_dir) if isfile(join(file_dir, f))]

        my_items_id = sb.get_my_items_id()
        # Creating new item from shapefile upload
        item = sb.upload_files_and_upsert_item({'parentId': my_items_id}, files, scrape_file=False)
        # Delete the item before the assertions to make sure it gets deleted
        sb.delete_item(item)
        self.assertIsNotNone(item)
        self.assertIsNotNone(item['files'])
        self.assertFalse('facets' in item)

    def test_upload_shapefile_individual_no_scrape(self):
        sb = SbSession('beta').login(self.TEST_USER, self.TEST_PASSWORD)
        file_dir = 'test/data/FHP_Great_Lakes_Basin_boundary'
        files = ["%s/%s" % (file_dir, f) for f in listdir(file_dir) if isfile(join(file_dir, f))]

        # Updating existing item with shapefile, uploading files individually

        item = sb.create_item({'parentId': sb.get_my_items_id(), 'title':'Pysb Shapefile Upload Test'})
        for f in files:
            item = sb.upload_file_to_item(item, f, scrape_file=False)
        # Delete the item before the assertions to make sure it gets deleted
        sb.delete_item(item)
        self.assertIsNotNone(item)
        self.assertIsNotNone(item['files'])
        self.assertFalse('facets' in item)

    def test_add_delete_user_acl(self):
        sb = SbSession('beta').login(self.TEST_USER, self.TEST_PASSWORD)
        item = sb.create_item({'title': "ACL Test", 'parentId': sb.get_my_items_id()})
        acls = sb.get_permissions(item['id'])
        self.assertFalse('USER:wilsonl@usgs.gov' in acls['read']['acl'])
        self.assertFalse('USER:wilsonl@usgs.gov' in acls['write']['acl'])

        sb.add_acl_user_read("wilsonl@usgs.gov", item['id'])
        acls = sb.add_acl_user_write("wilsonl@usgs.gov", item['id'])
        self.assertTrue('USER:wilsonl@usgs.gov' in acls['read']['acl'])
        self.assertTrue('USER:wilsonl@usgs.gov' in acls['write']['acl'])

        sb.remove_acl_user_read("wilsonl@usgs.gov", item['id'])
        acls = sb.remove_acl_user_write("wilsonl@usgs.gov", item['id'])
        self.assertFalse('USER:wilsonl@usgs.gov' in acls['read']['acl'])
        self.assertFalse('USER:wilsonl@usgs.gov' in acls['write']['acl'])

        sb.delete_item(item)

    def test_add_delete_role_acl(self):
        sb = SbSession('beta').login(self.TEST_USER, self.TEST_PASSWORD)
        item = sb.create_item({'title': "ACL Test", 'parentId': sb.get_my_items_id()})
        acls = sb.get_permissions(item['id'])
        self.assertFalse('ROLE:ScienceBase_DataAdmin' in acls['read']['acl'])
        self.assertFalse('ROLE:ScienceBase_DataAdmin' in acls['write']['acl'])

        sb.add_acl_role_read("ScienceBase_DataAdmin", item['id'])
        acls = sb.add_acl_role_write("ScienceBase_DataAdmin", item['id'])
        self.assertTrue('ROLE:ScienceBase_DataAdmin' in acls['read']['acl'])
        self.assertTrue('ROLE:ScienceBase_DataAdmin' in acls['write']['acl'])
    
        sb.remove_acl_role_read("ScienceBase_DataAdmin", item['id'])
        acls = sb.remove_acl_role_write("ScienceBase_DataAdmin", item['id'])
        self.assertFalse('ROLE:ScienceBase_DataAdmin' in acls['read']['acl'])
        self.assertFalse('ROLE:ScienceBase_DataAdmin' in acls['write']['acl'])

        sb.delete_item(item)
    
    def test_has_public_read(self):
        sb = SbSession('beta').login(self.TEST_USER, self.TEST_PASSWORD)
        acls = sb.get_permissions(sb.get_my_items_id())
        self.assertFalse(sb.has_public_read(acls))
        # smoke test print_acls
        sb.print_acls(acls)

    def test_relationships(self):
        sb = SbSession('beta').login(self.TEST_USER, self.TEST_PASSWORD)
        item1 = sb.create_item({'title': "Project", 'parentId': sb.get_my_items_id()})
        item2 = sb.create_item({'title': "Product", 'parentId': sb.get_my_items_id()})
        result = sb.create_related_item_link(item1['id'], item2['id'])
        self.assertTrue(result['itemId'] == item1['id'])
        self.assertTrue(result['relatedItemId'] == item2['id'])

        sb.delete_item(item1)
        sb.delete_item(item2)

if __name__ == '__main__':
    unittest.main()