"""
Test module for Yahoo Finance scraper
"""
import unittest
from unittest.mock import patch, MagicMock
from src.scrapers.yahoo_scraper import YahooFinanceScraper

class TestYahooFinanceScraper(unittest.TestCase):
    """Test case for YahooFinanceScraper"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.scraper = YahooFinanceScraper(delay=0)  # No delay for testing
    
    @patch('src.scrapers.yahoo_scraper.make_request')
    def test_scrape_data_success(self, mock_make_request):
        """Test successful data scraping"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <body>
                <table>
                    <tr>
                        <td>P/E Ratio (TTM)</td>
                        <td>25.6</td>
                    </tr>
                    <tr>
                        <td>Price/Book (MRQ)</td>
                        <td>15.2</td>
                    </tr>
                    <tr>
                        <td>Price/Sales (TTM)</td>
                        <td>7.9</td>
                    </tr>
                    <tr>
                        <td>Forward P/E</td>
                        <td>22.4</td>
                    </tr>
                </table>
            </body>
        </html>
        """
        mock_make_request.return_value = mock_response
        
        # Call the method
        result = self.scraper._scrape_data('AAPL')
        
        # Verify the results
        self.assertIn('P/E Ratio (Yahoo)', result)
        self.assertEqual(result['P/E Ratio (Yahoo)'], '25.6')
        self.assertIn('P/B Ratio (Yahoo)', result)
        self.assertEqual(result['P/B Ratio (Yahoo)'], '15.2')
        self.assertIn('P/S Ratio (Yahoo)', result)
        self.assertEqual(result['P/S Ratio (Yahoo)'], '7.9')
        self.assertIn('Forward P/E (Yahoo)', result)
        self.assertEqual(result['Forward P/E (Yahoo)'], '22.4')
    
    @patch('src.scrapers.yahoo_scraper.make_request')
    def test_scrape_data_empty(self, mock_make_request):
        """Test scraping with no data found"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <body>
                <table>
                    <tr>
                        <td>Some other metric</td>
                        <td>42</td>
                    </tr>
                </table>
            </body>
        </html>
        """
        mock_make_request.return_value = mock_response
        
        # Call the method
        result = self.scraper._scrape_data('AAPL')
        
        # Verify the results
        self.assertEqual(result, {})

if __name__ == '__main__':
    unittest.main()