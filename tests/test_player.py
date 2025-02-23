import unittest
from literature_game.player import Player
from literature_game.card import Card

class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.player = Player("Test Player", 1)
        self.test_card = Card('Hearts', 'Ace')
    
    def test_init(self):
        """Test player initialization"""
        self.assertEqual(self.player.name, "Test Player")
        self.assertEqual(self.player.id, 1)
        self.assertEqual(len(self.player.hand), 0)
    
    def test_add_card(self):
        """Test adding cards to hand"""
        self.player.add_card(self.test_card)
        self.assertEqual(len(self.player.hand), 1)
        self.assertEqual(self.player.hand[0], self.test_card)
    
    def test_show_hand(self):
        """Test hand display"""
        self.player.add_card(self.test_card)
        hand = self.player.show_hand()
        self.assertEqual(hand, ['Ace of Hearts'])
    
    def test_has_root_card(self):
        """Test root card checking"""
        self.player.add_card(self.test_card)
        self.assertTrue(self.player.has_root_card(self.test_card.get_set()))
        
    def test_get_set_cards(self):
        """Test getting cards from a set"""
        self.player.add_card(self.test_card)
        set_cards = self.player.get_set_cards(self.test_card.get_set())
        self.assertEqual(len(set_cards), 1)
        self.assertEqual(set_cards[0], self.test_card) 