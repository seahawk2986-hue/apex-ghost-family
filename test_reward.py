import unittest

class TestReward(unittest.TestCase):
    def test_calculate_reward(self):
        # Mock data and expected result
        user_points = 100
        reward_rate = 0.1
        expected_reward = 10
        
        # Call the function to be tested
        calculated_reward = calculate_reward(user_points, reward_rate)
        
        # Assert that the calculated reward matches the expected reward
        self.assertEqual(calculated_reward, expected_reward)

def calculate_reward(points, rate):
    return points * rate

if __name__ == '__main__':
    unittest.main()