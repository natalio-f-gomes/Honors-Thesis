import unittest


class TestErrorHandling(unittest.TestCase):
    """Tewt eror handling patterns"""
    
    def test_user_not_found(self):
        """Test handling when user/resume not found"""
        def get_item(items, item_id):
            for item in items:
                if item['id'] == item_id:
                    return item
            return None
        
        items = [{'id': '1'}, {'id': '2'}]
        
        result = get_item(items, '3')
        self.assertIsNone(result)
    
    def test_item_found(self):
        """Test successful item retrieval"""
        def get_item(items, item_id):
            for item in items:
                if item['id'] == item_id:
                    return item
            return None
        
        items = [{'id': '1', 'name': 'Item 1'}, {'id': '2', 'name': 'Item 2'}]
        
        result = get_item(items, '1')
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'Item 1')
    
    def test_empty_list_search(self):
        """Test searching in empty list"""
        def get_item(items, item_id):
            for item in items:
                if item['id'] == item_id:
                    return item
            return None
        
        items = []
        
        result = get_item(items, 'any-id')
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
