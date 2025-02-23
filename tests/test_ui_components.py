from kivy.tests.common import GraphicUnitTest
from literature_game.gui.components.player_hand import PlayerHand
from literature_game.gui.components.game_table import GameTable
from literature_game.player import Player
from literature_game.game_state import GameState

class TestUIComponents(GraphicUnitTest):
    def setUp(self):
        super().setUp()
        self.player = Player("Test Player", 0)
        self.game_state = GameState([self.player])
    
    def test_player_hand(self):
        """Test player hand widget"""
        hand = PlayerHand(self.player)
        self.assertEqual(hand.player, self.player)
        self.assertEqual(len(hand.cards), 0)
    
    def test_game_table(self):
        """Test game table widget"""
        table = GameTable()
        self.assertEqual(len(table.hands), 0)
        table.setup_game(self.game_state)
        self.assertEqual(len(table.hands), 1) 