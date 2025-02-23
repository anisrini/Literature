import unittest
from literature_game.card import Card

class TestCard(unittest.TestCase):
    def setUp(self):
        self.card = Card('Hearts', 'Ace')
    
    def test_init(self):
        """Test card initialization"""
        self.assertEqual(self.card.suit, 'Hearts')
        self.assertEqual(self.card.rank, 'Ace')
    
    def test_get_symbol(self):
        """Test suit symbol generation"""
        self.assertEqual(self.card.get_symbol(), '♥')
        spade_card = Card('Spades', '2')
        self.assertEqual(spade_card.get_symbol(), '♠')
    
    def test_get_short_rank(self):
        """Test rank shortening"""
        self.assertEqual(self.card.get_short_rank(), 'A')
        ten_card = Card('Hearts', '10')
        self.assertEqual(ten_card.get_short_rank(), '10')
        king_card = Card('Hearts', 'King')
        self.assertEqual(king_card.get_short_rank(), 'K')
    
    def test_str(self):
        """Test string representation"""
        self.assertEqual(str(self.card), 'Ace of Hearts')
    
    def test_equality(self):
        """Test card equality"""
        same_card = Card('Hearts', 'Ace')
        different_card = Card('Spades', 'Ace')
        self.assertEqual(self.card, same_card)
        self.assertNotEqual(self.card, different_card)
        self.assertNotEqual(self.card, "Not a card") 