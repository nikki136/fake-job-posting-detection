import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urlparse
import socket
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set default timeout for socket operations
socket.setdefaulttimeout(10)

# Disable SSL warnings
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass

class JobScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.timeout = 15
    
    def check_url_reachable(self, url):
        """Quick check if URL is reachable before attempting full scrape"""
        try:
            logger.info(f"Checking reachability for URL: {url}")
            
            # Parse the URL to get hostname
            parsed = urlparse(url)
            hostname = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            
            logger.info(f"Connecting to {hostname}:{port}")
            
            # Attempt to connect to the host
            sock = socket.create_connection((hostname, port), timeout=5)
            sock.close()
            logger.info(f"Successfully connected to {hostname}:{port}")
            return True
        except socket.gaierror as e:
            # DNS resolution failed
            logger.warning(f"DNS resolution failed for {url}: {str(e)}")
            return False
        except socket.timeout as e:
            # Connection timed out
            logger.warning(f"Connection timeout for {url}: {str(e)}")
            return False
        except Exception as e:
            # Other connection errors
            logger.warning(f"Connection error for {url}: {str(e)}")
            return False
    
    def test_url_accessibility(self, url):
        """Test if a URL is accessible by making a HEAD request"""
        try:
            logger.info(f"Testing URL accessibility: {url}")
            
            # Enhanced headers to avoid blocking
            enhanced_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Make HEAD request first
            response = requests.head(url, headers=enhanced_headers, timeout=10, verify=False)
            
            # If HEAD request fails with 405 (Method Not Allowed), try GET with small range
            if response.status_code == 405:
                logger.info(f"HEAD request not allowed, trying GET with range for: {url}")
                enhanced_headers['Range'] = 'bytes=0-1023'  # Only request first 1KB
                response = requests.get(url, headers=enhanced_headers, timeout=10, verify=False)
            
            logger.info(f"URL {url} returned status code: {response.status_code}")
            return response.status_code
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception for URL {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error testing URL {url}: {str(e)}")
            return None
    
    def is_valid_url(self, url):
        """Check if URL is valid and from supported job portals"""
        try:
            # Strip whitespace
            url = url.strip()
            
            # Check if URL is empty
            if not url:
                logger.warning("URL is empty")
                return False
            
            # Check if URL starts with http or https
            if not url.startswith(('http://', 'https://')):
                logger.warning(f"URL missing protocol: {url}")
                return False
            
            result = urlparse(url)
            logger.info(f"Parsed URL: {result}")
            
            # Check if scheme and netloc are present
            if not all([result.scheme, result.netloc]):
                logger.warning(f"Invalid URL - missing scheme or netloc: {url}")
                return False
            
            # Check if scheme is http or https
            if result.scheme not in ['http', 'https']:
                logger.warning(f"Invalid URL scheme: {result.scheme}")
                return False
            
            # Check if URL appears to be a job posting
            job_portals = ['linkedin.com', 'naukri.com', 'google.com/jobs', 'indeed.com', 'glassdoor.com', 'monster.com', 'ziprecruiter.com', 'careerbuilder.com']
            if not any(portal in url for portal in job_portals):
                # Check if URL contains job-related keywords
                job_keywords = ['job', 'career', 'employment', 'position', 'opening', 'vacancy', 'work']
                if not any(keyword in url.lower() for keyword in job_keywords):
                    logger.warning(f"URL does not appear to be a job posting: {url}")
                    return False
            logger.info(f"URL appears to be a job posting: {url}")
            return True
            
            # Check if netloc looks reasonable
            if len(result.netloc) < 3 or '.' not in result.netloc:
                logger.warning(f"Invalid URL netloc: {result.netloc}")
                return False
                
            # Check for common invalid characters
            invalid_chars = ['<', '>', '"', '{}', '|', '\\', '^', '`']
            if any(char in url for char in invalid_chars):
                logger.warning(f"URL contains invalid characters: {url}")
                return False
                
            logger.info(f"URL is valid: {url}")
            return True
        except Exception as e:
            logger.error(f"Error validating URL {url}: {str(e)}")
            return False
    
    def clean_text(self, text):
        """Clean extracted text"""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?-]', '', text)
        
        return text
    
    def extract_job_content(self, url):
        """Extract job posting content from URL"""
        try:
            logger.info(f"Attempting to scrape URL: {url}")
            
            if not self.is_valid_url(url):
                logger.warning(f"Invalid URL format: {url}")
                return {"error": "Invalid URL format"}
            
            # Quick reachability check
            logger.info(f"Checking URL reachability: {url}")
            if not self.check_url_reachable(url):
                logger.warning(f"URL not reachable: {url}")
                return {"error": "Website appears to be unreachable. Please check the URL or your internet connection."}
            
            # Enhanced headers to avoid blocking, with special handling for job sites
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            
            # Special handling for LinkedIn and Naukri
            if 'linkedin.com' in url:
                user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            elif 'naukri.com' in url:
                user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            
            enhanced_headers = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
            
            # Make HEAD request first to check if page exists without downloading content
            logger.info(f"Making HEAD request to check if page exists: {url}")
            head_response = requests.head(url, headers=enhanced_headers, timeout=10, verify=False)
            
            # If HEAD request fails, try GET request
            if head_response.status_code >= 400:
                logger.info(f"HEAD request failed, trying GET request: {url}")
                head_response = requests.get(url, headers=enhanced_headers, timeout=self.timeout, verify=False)
            
            # Check if page exists
            if head_response.status_code == 404:
                logger.warning(f"Page not found (404) for URL: {url}")
                # Return fake job data instead of error for 404s
                return {
                    'title': 'Job Not Found',
                    'company': 'Unknown Company',
                    'location': 'Unknown Location',
                    'description': 'This job posting could not be found. The URL may be invalid or the job posting may have been removed.',
                    'requirements': '',
                    'benefits': '',
                    'posted_date': '',
                    'full_content': 'This job posting could not be found. The URL may be invalid or the job posting may have been removed.',
                    'url': url
                }
            elif head_response.status_code == 403:
                logger.warning(f"Access forbidden (403) for URL: {url}")
                return {"error": f"Access to the job posting page is forbidden (403 error) at URL: {url}. The website may be blocking automated access."}
            elif head_response.status_code >= 400:
                logger.warning(f"HTTP error {head_response.status_code} for URL: {url}")
                return {"error": f"HTTP error: {head_response.status_code} at URL: {url}"}
            
            # If we get here, the page exists, so proceed with full GET request
            logger.info(f"Making full HTTP request to: {url}")
            response = requests.get(url, headers=enhanced_headers, timeout=self.timeout, verify=False)
            response.raise_for_status()
            
            # Parse HTML
            logger.info(f"Parsing HTML content from: {url}")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "advertisement"]):
                element.decompose()
            
            # Special handling for Google job links
            if 'google.com' in url:
                # For Google jobs, try to preserve more structured content
                # Remove only the most intrusive elements
                for element in soup(["script", "style", "nav", "footer", "header", "aside", "advertisement", "noscript"]):
                    element.decompose()
                
                # Extract text content
                text_content = soup.get_text(separator=' ', strip=True)
                cleaned_content = self.clean_text(text_content)
            else:
                # Standard processing for other job sites
                # Remove unwanted elements
                for element in soup(["script", "style", "nav", "footer", "header", "aside", "advertisement"]):
                    element.decompose()
                
                # Extract text content
                text_content = soup.get_text(separator=' ', strip=True)
                cleaned_content = self.clean_text(text_content)
            
            # Special handling for Google job links
            if 'google.com' in url:
                logger.info(f"Using Google-specific extraction for: {url}")
                job_data = self.extract_google_job_details(soup, url)
                job_data['full_content'] = cleaned_content
                job_data['url'] = url
            else:
                # Try to extract specific job posting elements
                job_data = self.extract_job_details(soup, url)
                job_data['full_content'] = cleaned_content
                job_data['url'] = url
                
                # If no meaningful content found, try alternative extraction
                # Special handling for Google job links - allow shorter content
                content_length = len(cleaned_content.strip())
                if content_length < 50:
                    # For Google jobs, allow as few as 20 characters
                    if 'google.com' in url and content_length >= 20:
                        # Continue with extracted data for Google jobs with at least 20 characters
                        pass
                    else:
                        logger.info(f"Using alternative extraction for: {url}")
                        job_data = self.alternative_extraction(soup, url)
            
            logger.info(f"Successfully scraped URL: {url}")
            return job_data
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout error for URL: {url}")
            return {"error": "Request timeout - website took too long to respond"}
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for URL: {url}")
            return {"error": "Connection error - unable to reach the website"}
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code} for URL: {url}")
            if e.response.status_code == 404:
                logger.warning(f"Page not found (404) for URL: {url}")
                # Return fake job data instead of error for 404s
                return {
                    'title': 'Job Not Found',
                    'company': 'Unknown Company',
                    'location': 'Unknown Location',
                    'description': 'This job posting could not be found. The URL may be invalid or the job posting may have been removed.',
                    'requirements': '',
                    'benefits': '',
                    'posted_date': '',
                    'full_content': 'This job posting could not be found. The URL may be invalid or the job posting may have been removed.',
                    'url': url
                }
            elif e.response.status_code == 403:
                return {"error": f"Access to the job posting page is forbidden (403 error) at URL: {url}. The website may be blocking automated access."}
            elif e.response.status_code >= 500:
                return {"error": f"The website server encountered an error ({e.response.status_code}) at URL: {url}. Please try again later."}
            else:
                return {"error": f"HTTP error: {e.response.status_code} at URL: {url}"}
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {str(e)}")
            return {"error": f"Error scraping content: {str(e)}"}
    
    def extract_job_details(self, soup, url):
        """Extract specific job posting details"""
        job_data = {
            'title': 'Not specified',
            'company': 'Not specified',
            'location': 'Not specified',
            'description': '',
            'requirements': '',
            'benefits': '',
            'posted_date': 'Not specified'
        }
        
        # Common selectors for job posting elements (expanded for various job boards)
        title_selectors = [
            'h1.topcard__title', '.topcard__title', '.jobTitle', '.jd-header-title',
            'h1', '.job-title', '.job-header-title', 
            '[data-testid="job-title"]', '.jobsearch-JobInfoHeader-title',
            '.job-header h1', '.jobHeader h1', '.job-title-heading',
            '.title', '.job-posting-title', '.posting-title',
            '.jobTitle', '.JobTitle', '.job_title',
            '.job-post-title', '.position-title',
            '.heading-large', '.job_heading', '.jobHeader h2'
        ]
        
        company_selectors = [
            '.topcard__org-name-link', '.jd-header-comp-name', '.company-info',
            '.company-name', '.employer-name', '.job-company',
            '[data-testid="company-name"]', '.jobsearch-InlineCompanyRating',
            '.company', '.employer', '.organization',
            '.jobs-details-top-card__company-url', '.job-company-name',
            '.companyName', '.employerName', '.org-name',
            '.job-employer', '.employer-title',
            '.company-title', '.employer-info', '.orgInfo',
            '.companyNameText', '.employer-name-text'
        ]
        
        location_selectors = [
            '.job-location', '.loc', '[data-testid="job-location"]',
            '.jobsearch-JobInfoHeader-subtitle', 
            '.jobs-details-top-card__job-info li',
            '.job-location', '.jobLocation', '.locationName',
            '.job-posting-location', '.posting-location',
            '.jobLoc', '.location-info', '.locInfo',
            '.job-location-text', '.location-text',
            '.locationText', '.job-location-display'
        ]
        
        # Special handling for Google job links
        if 'google.com' in url:
            # Try Google-specific selectors first
            google_title = soup.select_one('h2.Ii1BCd') or soup.select_one('.heading-large')
            if google_title:
                text = self.clean_text(google_title.get_text())
                if text and not any(ignore in text.lower() for ignore in ['sign in', 'log in', 'access ai', 'week ago', 'days ago', 'month ago']) and \
                   not any(company_word in text.lower() for company_word in ['inc', 'llc', 'ltd', 'corp', 'corporation', 'limited', 'company']) and \
                   len(text) > 3:
                    job_data['title'] = text
        
        # Extract title (prioritize this first)
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                text = self.clean_text(element.get_text())
                # Filter out common non-title text and ensure it doesn't look like a company
                if text and not any(ignore in text.lower() for ignore in ['sign in', 'log in', 'access ai', 'week ago', 'days ago', 'month ago']) and \
                   not any(company_word in text.lower() for company_word in ['inc', 'llc', 'ltd', 'corp', 'corporation', 'limited', 'company']) and \
                   len(text) > 3:  # Ensure it's not too short
                    job_data['title'] = text
                    break
        
        # Special handling for LinkedIn job titles
        if not job_data['title']:
            linkedin_title = soup.select_one('h1.topcard__title')
            if linkedin_title:
                text = self.clean_text(linkedin_title.get_text())
                if text and not any(ignore in text.lower() for ignore in ['sign in', 'log in', 'access ai', 'week ago', 'days ago', 'month ago']) and \
                   not any(company_word in text.lower() for company_word in ['inc', 'llc', 'ltd', 'corp', 'corporation', 'limited', 'company']) and \
                   len(text) > 3:  # Ensure it's not too short
                    job_data['title'] = text
        
        # Fallback: Try to get the first h1 that looks like a job title
        if not job_data['title'] or job_data['title'] == 'Not specified':
            h1_elements = soup.find_all('h1')
            for element in h1_elements:
                text = self.clean_text(element.get_text())
                if text and not any(ignore in text.lower() for ignore in ['sign in', 'log in', 'access ai', 'week ago', 'days ago', 'month ago']) and \
                   not any(company_word in text.lower() for company_word in ['inc', 'llc', 'ltd', 'corp', 'corporation', 'limited', 'company']) and \
                   len(text) > 3 and len(text) < 100:  # Reasonable length
                    job_data['title'] = text
                    break
            
            # Ultimate fallback for job title
            if not job_data['title'] or job_data['title'] == 'Not specified':
                # Try any h1 or h2 element
                header_elements = soup.find_all(['h1', 'h2'])
                for element in header_elements:
                    text = self.clean_text(element.get_text())
                    if text and len(text) > 3 and len(text) < 100 and \
                       not any(ignore in text.lower() for ignore in ['sign in', 'log in', 'access ai', 'week ago', 'days ago', 'month ago']) and \
                       not any(company_word in text.lower() for company_word in ['inc', 'llc', 'ltd', 'corp', 'corporation', 'limited', 'company']):
                        job_data['title'] = text
                        break
        
        # Special handling for Google job links
        if 'google.com' in url:
            # Try Google-specific selectors first
            google_company = soup.select_one('.nJlQNd') or soup.select_one('.sMzDkb')
            if google_company:
                text = self.clean_text(google_company.get_text())
                if text and not any(ignore in text.lower() for ignore in ['sign in', 'log in', 'access ai', 'see full content', 'week ago', 'days ago', 'month ago', 'analyst', 'manager', 'developer']) and \
                   (any(company_word in text.lower() for company_word in ['inc', 'llc', 'ltd', 'corp', 'corporation', 'limited', 'company']) or (len(text.split()) <= 4 and ' ' in text)):
                    job_data['company'] = text
        
        # Extract company (be more selective)
        for selector in company_selectors:
            element = soup.select_one(selector)
            if element:
                text = self.clean_text(element.get_text())
                # Filter out common non-company text and ensure it looks like a company
                if text and not any(ignore in text.lower() for ignore in ['sign in', 'log in', 'access ai', 'see full content', 'week ago', 'days ago', 'month ago', 'analyst', 'manager', 'developer']) and \
                   (any(company_word in text.lower() for company_word in ['inc', 'llc', 'ltd', 'corp', 'corporation', 'limited', 'company']) or (len(text.split()) <= 4 and ' ' in text)):
                    job_data['company'] = text
                    break
        
        # Special handling for LinkedIn companies
        if not job_data['company']:
            linkedin_company = soup.select_one('a.topcard__org-name-link')
            if linkedin_company:
                text = self.clean_text(linkedin_company.get_text())
                if text and not any(ignore in text.lower() for ignore in ['sign in', 'log in', 'access ai', 'see full content', 'week ago', 'days ago', 'month ago', 'analyst', 'manager', 'developer']):
                    job_data['company'] = text
        
        # Special handling for Naukri companies
        if not job_data['company']:
            naukri_company = soup.select_one('.jd-header-comp-name')
            if naukri_company:
                text = self.clean_text(naukri_company.get_text())
                if text and not any(ignore in text.lower() for ignore in ['sign in', 'log in', 'access ai', 'see full content', 'week ago', 'days ago', 'month ago', 'analyst', 'manager', 'developer']):
                    job_data['company'] = text
        
        # Special handling for Google job links
        if 'google.com' in url:
            # Try Google-specific selectors first
            google_location = soup.select_one('.lc0RId') or soup.select_one('.locationText')
            if google_location:
                text = self.clean_text(google_location.get_text())
                if text and not any(ignore in text.lower() for ignore in ['sign in', 'log in', 'access ai', 'see full content', 'week ago', 'days ago', 'month ago', 'posted', 'analyst', 'manager', 'developer', 'intern', 'associate', 'specialist']) and \
                   (',' in text or 
                    any(loc_indicator in text.lower() for loc_indicator in ['city', 'state', 'county', 'country', 'remote', 'hybrid', 'onsite', 'office', 'headquarters', 'hq']) or
                    # Also accept locations with common geographic patterns
                    (len(text.split()) <= 3 and any(char.isalpha() for char in text) and not text.isdigit())):
                    job_data['location'] = text
        
        # Extract location (avoid date text and job titles)
        for selector in location_selectors:
            element = soup.select_one(selector)
            if element:
                text = self.clean_text(element.get_text())
                # Filter out common non-location text, date text, and job titles
                if text and not any(ignore in text.lower() for ignore in ['sign in', 'log in', 'access ai', 'see full content', 'week ago', 'days ago', 'month ago', 'posted', 'analyst', 'manager', 'developer', 'intern', 'associate', 'specialist']) and \
                   (',' in text or 
                    any(loc_indicator in text.lower() for loc_indicator in ['city', 'state', 'county', 'country', 'remote', 'hybrid', 'onsite', 'office', 'headquarters', 'hq']) or
                    # Also accept locations with common geographic patterns
                    (len(text.split()) <= 3 and any(char.isalpha() for char in text) and not text.isdigit())):
                    job_data['location'] = text
                    break
        
        # Special handling for LinkedIn locations
        if not job_data['location']:
            linkedin_location_elements = soup.select('.jobs-details-top-card__job-info li')
            for element in linkedin_location_elements:
                text = self.clean_text(element.get_text())
                # LinkedIn locations often have specific patterns
                if text and \
                   not any(ignore in text.lower() for ignore in ['sign in', 'log in', 'access ai', 'see full content', 'week ago', 'days ago', 'month ago', 'posted', 'analyst', 'manager', 'developer', 'intern', 'associate', 'specialist']) and \
                   (',' in text or 
                    any(loc_indicator in text.lower() for loc_indicator in ['city', 'state', 'county', 'country', 'remote', 'hybrid', 'onsite', 'office', 'headquarters', 'hq']) or
                    # Also accept locations with common geographic patterns
                    (len(text.split()) <= 3 and any(char.isalpha() for char in text) and not text.isdigit())):
                    job_data['location'] = text
                    break
        
        # Fallback location extraction for Naukri
        if not job_data['location']:
            naukri_location = soup.select_one('.loc')
            if naukri_location:
                text = self.clean_text(naukri_location.get_text())
                if text and \
                   not any(ignore in text.lower() for ignore in ['sign in', 'log in', 'access ai', 'see full content', 'week ago', 'days ago', 'month ago', 'posted', 'analyst', 'manager', 'developer', 'intern', 'associate', 'specialist']) and \
                   (',' in text or 
                    any(loc_indicator in text.lower() for loc_indicator in ['city', 'state', 'county', 'country', 'remote', 'hybrid', 'onsite', 'office', 'headquarters', 'hq'])):
                    job_data['location'] = text
        
        # Extract posted date
        date_selectors = [
            '.posted-date', '.date', '.time', '.posted',
            '[data-testid="job-post-date"]', '.job-posted-date',
            '.topcard__flavor--metadata', '.job-date',
            'time', '.post-date', '.postedOn', '.datePosted',
            '.jobPostDate', '.posting-date', '.date-posted',
            '.job-date-info', '.dateInfo'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                text = self.clean_text(element.get_text())
                if text and ('ago' in text.lower() or 'day' in text.lower() or 'week' in text.lower() or 'month' in text.lower()):
                    job_data['posted_date'] = text
                    break
        
        # Special handling for LinkedIn dates
        if not job_data['posted_date']:
            linkedin_date = soup.select_one('span.topcard__flavor--metadata')
            if linkedin_date:
                text = self.clean_text(linkedin_date.get_text())
                if text and ('ago' in text.lower() or 'day' in text.lower() or 'week' in text.lower() or 'month' in text.lower()):
                    job_data['posted_date'] = text
        
        # Extract description (usually the largest text block)
        description_selectors = [
            '.job-description', '.job-summary', '.description',
            '[data-testid="job-description"]', '.jobsearch-jobDescriptionText',
            '.show-more-less-html__markup', '.job-desc', '.job_description',
            '#job-details', '.job-desc-main'
        ]
        
        for selector in description_selectors:
            element = soup.select_one(selector)
            if element:
                job_data['description'] = self.clean_text(element.get_text())
                break
        
        # Special handling for LinkedIn descriptions
        if not job_data['description']:
            linkedin_desc = soup.select_one('.show-more-less-html__markup')
            if linkedin_desc:
                job_data['description'] = self.clean_text(linkedin_desc.get_text())
        
        # Special handling for Naukri descriptions
        if not job_data['description']:
            naukri_desc = soup.select_one('.job-desc')
            if naukri_desc:
                job_data['description'] = self.clean_text(naukri_desc.get_text())
        
        return job_data
    
    def alternative_extraction(self, soup, url):
        """Alternative extraction method for difficult websites"""
        job_data = {
            'title': 'Not specified',
            'company': 'Not specified',
            'location': 'Not specified',
            'description': '',
            'requirements': '',
            'benefits': '',
            'posted_date': 'Not specified',
            'full_content': '',
            'url': url
        }
        
        # Try to get any meaningful text from common containers
        content_selectors = [
            '.main-content', '.content', '.job-content', '.jd-container',
            '.job-description', '.job-details', '.posting-content',
            'main', 'article', '.primary-content', '.job-posting',
            '.job-main', '.job-body', '.job-view-layout',
            '.job-details-page', '.job-posting-details',
            '.jobContent', '.jobDesc', '.job-detail',
            '.jobView', '.jobListing', '.job-post',
            '.job-post-content', '.job-post-body', '.job-post-main',
            '.job-posting-content', '.posting-body',
            '.iausVc', '.jobDescription', '[data-content-field="description"]'
        ]
        
        extracted_text = []
        
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(separator=' ', strip=True)
                if len(text) > 100:  # Only meaningful content
                    extracted_text.append(text)
        
        # If still no content, get all paragraph text
        if not extracted_text:
            paragraphs = soup.find_all(['p', 'div', 'span'])
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 50:
                    extracted_text.append(text)
        
        # Combine all extracted text
        combined_text = ' '.join(extracted_text[:10])  # Limit to first 10 meaningful chunks
        job_data['full_content'] = self.clean_text(combined_text)
        job_data['description'] = job_data['full_content'][:500] + '...' if len(job_data['full_content']) > 500 else job_data['full_content']
        
        # Special handling for Google job links
        if 'google.com' in url:
            # Try Google-specific selectors first
            google_title = soup.select_one('h2.Ii1BCd') or soup.select_one('.heading-large')
            if google_title:
                text = self.clean_text(google_title.get_text())
                if text and len(text) > 3:
                    job_data['title'] = text
        
        # Try to extract job title first (more specific selectors)
        title_selectors = [
            'h1.topcard__title', '.topcard__title', '.jobTitle', '.jd-header-title',
            'h1', '.job-title',
            '.jobTitle', '.JobTitle', '.job_title',
            '.job-header h1', '.jobHeader h1', '.job-title-heading',
            '.title', '.job-posting-title', '.posting-title',
            '.heading-large', '.job_heading', '.jobHeader h2'
        ]
        
        for selector in title_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if 5 < len(text) < 100 and not any(keyword in text.lower() for keyword in ['job', 'position', 'title', 'description', 'apply', 'sign', 'log in', 'access ai', 'company', 'employer']):
                    # Additional check to ensure this isn't a company name
                    if not any(company_keyword in text.lower() for company_keyword in ['inc', 'llc', 'ltd', 'corp', 'corporation', 'limited', 'company']):
                        job_data['title'] = self.clean_text(text)
                        break
            if job_data['title'] != 'Content extracted from page':
                break
        
        # Special handling for Google job links
        if 'google.com' in url:
            # Try Google-specific selectors first
            google_company = soup.select_one('.nJlQNd') or soup.select_one('.sMzDkb')
            if google_company:
                text = self.clean_text(google_company.get_text())
                if text and len(text) > 1:
                    job_data['company'] = text
        
        # Try to extract company name from common locations
        company_selectors = [
            '.topcard__org-name-link', '.jd-header-comp-name', '.company-info',
            '.company-name', '.employer', '.organization', '.job-company',
            'h2', 'h3',
            '.companyName', '.employerName', '.org-name',
            '.job-employer', '.employer-title',
            '.company-title', '.employer-info', '.orgInfo',
            '.companyNameText', '.employer-name-text', '.nJlQNd', '.sMzDkb'
        ]
        
        for selector in company_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                # Heuristic: company names often contain business entity identifiers or are shorter
                if 2 < len(text) < 50 and not any(keyword in text.lower() for keyword in ['job', 'position', 'title', 'description', 'apply', 'sign', 'log in', 'access ai', 'week ago', 'days ago', 'month ago']):
                    # Additional check to ensure this looks like a company name
                    if any(company_keyword in text.lower() for company_keyword in ['inc', 'llc', 'ltd', 'corp', 'corporation', 'limited', 'company']) or (len(text.split()) <= 4 and ' ' in text):
                        job_data['company'] = self.clean_text(text)
                        break
            if job_data['company'] != 'See full content below':
                break
        
        # Special handling for LinkedIn companies
        if job_data['company'] == 'See full content below':
            linkedin_company = soup.select_one('a.topcard__org-name-link')
            if linkedin_company:
                text = linkedin_company.get_text(strip=True)
                if 2 < len(text) < 50 and not any(keyword in text.lower() for keyword in ['job', 'position', 'title', 'description', 'apply', 'sign', 'log in', 'access ai', 'week ago', 'days ago', 'month ago']):
                    job_data['company'] = self.clean_text(text)
        
        # Special handling for Naukri companies
        if job_data['company'] == 'See full content below':
            naukri_company = soup.select_one('.jd-header-comp-name')
            if naukri_company:
                text = naukri_company.get_text(strip=True)
                if 2 < len(text) < 50 and not any(keyword in text.lower() for keyword in ['job', 'position', 'title', 'description', 'apply', 'sign', 'log in', 'access ai', 'week ago', 'days ago', 'month ago']):
                    job_data['company'] = self.clean_text(text)
        
        # Fallback company extraction from any element with company-like characteristics
        if job_data['company'] == 'See full content below' or not job_data['company'] or job_data['company'] == 'Not specified':
            # Look for elements that might contain company names
            potential_companies = soup.find_all(['h2', 'h3', 'h4', 'div', 'span', 'a'])
            for element in potential_companies:
                text = element.get_text(strip=True)
                # Check if this looks like a company name
                if 2 < len(text) < 50 and ' ' in text:
                    # Skip if it looks like a date or title
                    if not any(date_keyword in text.lower() for date_keyword in ['week ago', 'days ago', 'month ago', 'posted', 'apply']) and \
                       not any(title_keyword in text.lower() for title_keyword in ['job', 'position', 'title', 'description', 'analyst', 'manager', 'developer']) and \
                       (any(company_keyword in text.lower() for company_keyword in ['inc', 'llc', 'ltd', 'corp', 'corporation', 'limited', 'company']) or len(text.split()) <= 4):
                        job_data['company'] = self.clean_text(text)
                        break
            
            # Ultimate fallback for company name
            if not job_data['company'] or job_data['company'] == 'Not specified':
                # Try to find any element that looks like a company name
                all_elements = soup.find_all(['div', 'span', 'p', 'strong'])
                for element in all_elements:
                    text = element.get_text(strip=True)
                    # Look for company indicators
                    if 2 < len(text) < 50 and \
                       any(company_indicator in text.lower() for company_indicator in ['inc', 'llc', 'ltd', 'corp', 'corporation', 'limited', 'company']):
                        job_data['company'] = self.clean_text(text)
                        break
        
        # Last resort: Try to find any element with company-like text
        if not job_data['company']:
            all_elements = soup.find_all(['div', 'span', 'p'])
            for element in all_elements:
                text = element.get_text(strip=True)
                # Look for company indicators
                if 3 < len(text) < 50 and \
                   any(company_indicator in text.lower() for company_indicator in ['inc', 'llc', 'ltd', 'corp', 'corporation', 'limited', 'company']):
                    # Clean up the text to extract just the company name
                    job_data['company'] = self.clean_text(text)
                    break
        
        # Special handling for Google job links
        if 'google.com' in url:
            # Try Google-specific selectors first
            google_location = soup.select_one('.lc0RId') or soup.select_one('.locationText')
            if google_location:
                text = self.clean_text(google_location.get_text())
                if text and (',' in text or len(text.split()) <= 3):
                    job_data['location'] = text
        
        # Try to extract job location
        location_selectors = [
            '.job-location', '.loc', '.topcard__flavor--metadata',
            '.jobLocation', '.locationName', '.job-posting-location',
            '.posting-location',
            '.jobLoc', '.location-info', '.locInfo',
            '.job-location-text', '.location-text',
            '.locationText', '.job-location-display', '.lc0RId'
        ]
        
        for selector in location_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                # Location should not contain date-related words or job titles
                if 2 < len(text) < 50 and \
                   not any(keyword in text.lower() for keyword in ['job', 'position', 'title', 'description', 'apply', 'sign', 'log in', 'access ai', 'see full content', 'week ago', 'days ago', 'month ago', 'posted', 'analyst', 'manager', 'developer', 'engineer', 'specialist', 'intern', 'associate']) and \
                   (',' in text or 
                    any(loc_indicator in text.lower() for loc_indicator in ['city', 'state', 'county', 'country', 'remote', 'hybrid', 'onsite', 'office', 'headquarters', 'hq']) or
                    # Also accept locations with common geographic patterns
                    (len(text.split()) <= 3 and any(char.isalpha() for char in text) and not text.isdigit())):
                    job_data['location'] = self.clean_text(text)
                    break
            if job_data['location'] != 'Various':
                break
        
        # Fallback location extraction
        if job_data['location'] == 'Various' or not job_data['location']:
            location_elements = soup.find_all(['span', 'div', 'p', 'li', 'td'])
            for element in location_elements:
                text = element.get_text(strip=True)
                # Check if this looks like a location
                if 2 < len(text) < 50 and \
                   (',' in text or 
                    any(loc_indicator in text.lower() for loc_indicator in ['city', 'state', 'county', 'country', 'remote', 'hybrid', 'onsite', 'office', 'headquarters', 'hq']) or
                    # Also accept locations with common geographic patterns
                    (len(text.split()) <= 3 and any(char.isalpha() for char in text) and not text.isdigit())) and \
                   not any(keyword in text.lower() for keyword in ['job', 'position', 'title', 'description', 'apply', 'sign', 'log in', 'access ai', 'see full content', 'week ago', 'days ago', 'month ago', 'posted', 'analyst', 'manager', 'developer', 'engineer', 'intern', 'associate', 'specialist']):
                    job_data['location'] = self.clean_text(text)
                    break
            
            # Last resort: Try to find any element with location-like text
            if not job_data['location']:
                all_elements = soup.find_all(['div', 'span', 'p'])
                for element in all_elements:
                    text = element.get_text(strip=True)
                    # Look for location indicators
                    if 3 < len(text) < 50 and \
                       any(loc_indicator in text.lower() for loc_indicator in ['city', 'state', 'county', 'country', 'remote', 'hybrid', 'onsite', 'office', 'headquarters', 'hq', 'location']):
                        # Clean up the text to extract just the location
                        job_data['location'] = self.clean_text(text)
                        break
        
        # Special handling for LinkedIn locations in alternative extraction
        if job_data['location'] == 'Various':
            linkedin_location_elements = soup.select('.jobs-details-top-card__job-info li')
            for element in linkedin_location_elements:
                text = element.get_text(strip=True)
                # LinkedIn locations often have specific patterns
                if 2 < len(text) < 50 and \
                   not any(keyword in text.lower() for keyword in ['job', 'position', 'title', 'description', 'apply', 'sign', 'log in', 'access ai', 'see full content', 'week ago', 'days ago', 'month ago', 'posted', 'analyst', 'manager', 'developer', 'engineer', 'intern', 'associate', 'specialist']) and \
                   (',' in text or 
                    any(loc_indicator in text.lower() for loc_indicator in ['city', 'state', 'county', 'country', 'remote', 'hybrid', 'onsite', 'office', 'headquarters', 'hq'])):
                    job_data['location'] = self.clean_text(text)
                    break
        
        # Fallback location extraction for Naukri
        if job_data['location'] == 'Various':
            naukri_location = soup.select_one('.loc')
            if naukri_location:
                text = naukri_location.get_text(strip=True)
                if 2 < len(text) < 50 and \
                   not any(keyword in text.lower() for keyword in ['job', 'position', 'title', 'description', 'apply', 'sign', 'log in', 'access ai', 'see full content', 'week ago', 'days ago', 'month ago', 'posted', 'analyst', 'manager', 'developer', 'engineer', 'intern', 'associate', 'specialist']) and \
                   (',' in text or 
                    any(loc_indicator in text.lower() for loc_indicator in ['city', 'state', 'county', 'country', 'remote', 'hybrid', 'onsite', 'office', 'headquarters', 'hq'])):
                    job_data['location'] = self.clean_text(text)
        
        # Special handling for Google job links
        if 'google.com' in url:
            # Look for date elements in Google job listings
            date_elements = soup.find_all(['time', 'span', 'div'])
            for element in date_elements:
                text = element.get_text(strip=True)
                # Look for date patterns
                if re.search(r'\d+\s*(day|week|month|year)s?\s*ago', text.lower()) or \
                   any(date_word in text.lower() for date_word in ['today', 'yesterday']):
                    job_data['posted_date'] = self.clean_text(text)
                    break
        
        # Try to extract posted date
        date_selectors = [
            '.posted-date', '.job-date', '.topcard__flavor--metadata',
            '.date', '.time', '.posted',
            '[data-testid="job-post-date"]', '.job-posted-date',
            'time', '.post-date', '.postedOn', '.datePosted',
            '.jobPostDate', '.posting-date', '.date-posted',
            '.job-date-info', '.dateInfo'
        ]
        
        for selector in date_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                # More specific date pattern matching
                if ('ago' in text.lower() or 'day' in text.lower() or 'week' in text.lower() or 'month' in text.lower() or 
                    re.search(r'\d+\s*(day|week|month)s?\s*ago', text.lower())) and \
                   not any(keyword in text.lower() for keyword in ['job', 'position', 'title', 'description', 'apply', 'sign', 'log in', 'access ai', 'location']):
                    job_data['posted_date'] = self.clean_text(text)
                    break
            if job_data['posted_date']:
                break
        
        # Fallback date extraction
        if not job_data['posted_date']:
            date_elements = soup.find_all(['time', 'span', 'div', 'p'])
            for element in date_elements:
                text = element.get_text(strip=True)
                # Look for date patterns
                if re.search(r'\d+\s*(day|week|month|year)s?\s*ago', text.lower()) or \
                   any(date_word in text.lower() for date_word in ['today', 'yesterday']) and \
                   not any(keyword in text.lower() for keyword in ['job', 'position', 'title', 'description', 'apply', 'sign', 'log in', 'access ai', 'location', 'company']):
                    job_data['posted_date'] = self.clean_text(text)
                    break
            
            # Last resort: Try to find any element with date-like text
            if not job_data['posted_date']:
                all_elements = soup.find_all(['div', 'span', 'p', 'time'])
                for element in all_elements:
                    text = element.get_text(strip=True)
                    # Look for date indicators
                    if 3 < len(text) < 50 and \
                       any(date_indicator in text.lower() for date_indicator in ['posted', 'date', 'ago', 'day', 'week', 'month', 'year']):
                        # Clean up the text to extract just the date
                        job_data['posted_date'] = self.clean_text(text)
                        break
        
        # Ultimate fallback: Try to extract title and company from any header elements
        if job_data['title'] == 'Not specified' or job_data['company'] == 'Not specified':
            # Try to get job title from first h1
            if job_data['title'] == 'Not specified':
                h1_element = soup.find('h1')
                if h1_element:
                    text = self.clean_text(h1_element.get_text())
                    if text and len(text) > 3:
                        job_data['title'] = text
            
            # Try to get company from first h2 or strong element
            if job_data['company'] == 'Not specified':
                h2_elements = soup.find_all('h2')
                for element in h2_elements:
                    text = self.clean_text(element.get_text())
                    if text and len(text) > 1 and len(text.split()) <= 4:
                        job_data['company'] = text
                        break
                
                # If still not found, try strong elements
                if job_data['company'] == 'Not specified':
                    strong_elements = soup.find_all('strong')
                    for element in strong_elements:
                        text = self.clean_text(element.get_text())
                        # Look for company-like text
                        if text and len(text) > 1 and len(text.split()) <= 4 and \
                           not any(ignore in text.lower() for ignore in ['job', 'title', 'position', 'role', 'posted', 'date']):
                            job_data['company'] = text
                            break
        
        # Final fallback: Try to extract from meta tags
        if not job_data['title'] or not job_data['company'] or job_data['location'] == 'Various':
            # Try to get job details from meta tags
            meta_title = soup.find('meta', attrs={'property': 'og:title'}) or soup.find('meta', attrs={'name': 'title'})
            if meta_title and not job_data['title']:
                content = meta_title.get('content', '')
                if content and 'job' in content.lower():
                    # Simple heuristic: if it contains 'job', it's likely a job title
                    job_data['title'] = self.clean_text(content)
            
            meta_description = soup.find('meta', attrs={'property': 'og:description'}) or soup.find('meta', attrs={'name': 'description'})
            if meta_description and (not job_data['company'] or job_data['location'] == 'Various'):
                content = meta_description.get('content', '')
                # Try to extract company and location from description
                if content:
                    # Simple pattern matching for company and location
                    import re
                    company_match = re.search(r'(?:at|with)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', content)
                    if company_match and not job_data['company']:
                        job_data['company'] = company_match.group(1)
        
        # Ultimate fallback: Try to extract from any h1 or h2 elements
        if job_data['title'] == 'Not specified' or job_data['company'] == 'Not specified':
            # Try to get job title from first h1
            if job_data['title'] == 'Not specified':
                h1_element = soup.find('h1')
                if h1_element:
                    text = self.clean_text(h1_element.get_text())
                    if text and len(text) > 3:
                        job_data['title'] = text
            
            # Try to get company from first h2 or strong element
            if job_data['company'] == 'Not specified':
                h2_elements = soup.find_all('h2')
                for element in h2_elements:
                    text = self.clean_text(element.get_text())
                    if text and len(text) > 1 and len(text.split()) <= 4:
                        job_data['company'] = text
                        break
                
                # If still not found, try strong elements
                if job_data['company'] == 'Not specified':
                    strong_elements = soup.find_all('strong')
                    for element in strong_elements:
                        text = self.clean_text(element.get_text())
                        # Look for company-like text
                        if text and len(text) > 1 and len(text.split()) <= 4 and \
                           not any(ignore in text.lower() for ignore in ['job', 'title', 'position', 'role', 'posted', 'date']):
                            job_data['company'] = text
                            break
        
        return job_data
    
    def extract_google_job_details(self, soup, url):
        """Extract job details specifically from Google job listings"""
        job_data = {
            'title': 'Not specified',
            'company': 'Not specified',
            'location': 'Not specified',
            'description': '',
            'requirements': '',
            'benefits': '',
            'posted_date': 'Not specified'
        }
        
        # Google job title (often in h2.Ii1BCd or similar)
        title_element = soup.select_one('h2.Ii1BCd') or soup.select_one('.heading-large') or soup.select_one('h1')
        if title_element:
            text = self.clean_text(title_element.get_text())
            if text and len(text) > 3:
                job_data['title'] = text
        
        # Google company name (often in .nJlQNd or .sMzDkb)
        company_element = soup.select_one('.nJlQNd') or soup.select_one('.sMzDkb') or soup.select_one('.companyNameText')
        if company_element:
            text = self.clean_text(company_element.get_text())
            if text and len(text) > 1:
                job_data['company'] = text
        
        # Google location (often in .lc0RId or .locationText)
        location_element = soup.select_one('.lc0RId') or soup.select_one('.locationText') or soup.select_one('[data-icon="location"]')
        if location_element:
            text = self.clean_text(location_element.get_text())
            if text and (',' in text or len(text.split()) <= 3):
                job_data['location'] = text
        
        # Google job description (often in .iausVc or similar)
        description_element = soup.select_one('.iausVc') or soup.select_one('.jobDescription') or soup.select_one('[data-content-field="description"]')
        if description_element:
            text = self.clean_text(description_element.get_text())
            if text and len(text) > 50:
                job_data['description'] = text
        
        # Try to extract requirements from lists or sections
        requirements_section = soup.select_one('[data-content-field="qualifications"]') or soup.select_one('.requirements')
        if requirements_section:
            text = self.clean_text(requirements_section.get_text())
            if text:
                job_data['requirements'] = text
        
        # Try to extract posted date
        date_elements = soup.find_all(['time', 'span', 'div'])
        for element in date_elements:
            text = element.get_text(strip=True)
            # Look for date patterns
            if re.search(r'\d+\s*(day|week|month|year)s?\s*ago', text.lower()) or \
               any(date_word in text.lower() for date_word in ['today', 'yesterday']):
                job_data['posted_date'] = self.clean_text(text)
                break
        
        # If we still don't have good data, try alternative selectors
        if job_data['title'] == 'Not specified' or job_data['company'] == 'Not specified':
            # Try more generic selectors
            h1_element = soup.find('h1')
            if h1_element and job_data['title'] == 'Not specified':
                text = self.clean_text(h1_element.get_text())
                if text and len(text) > 3:
                    job_data['title'] = text
            
            h2_elements = soup.find_all('h2')
            if h2_elements and job_data['company'] == 'Not specified':
                for h2 in h2_elements:
                    text = self.clean_text(h2.get_text())
                    # If it looks like a company name
                    if text and len(text) > 1 and len(text.split()) <= 4:
                        job_data['company'] = text
                        break
            
            # Ultimate fallback for Google jobs
            if job_data['title'] == 'Not specified' or job_data['company'] == 'Not specified':
                # Try to get job title from first h1
                if job_data['title'] == 'Not specified':
                    h1_element = soup.find('h1')
                    if h1_element:
                        text = self.clean_text(h1_element.get_text())
                        if text and len(text) > 3:
                            job_data['title'] = text
                
                # Try to get company from first h2 or strong element
                if job_data['company'] == 'Not specified':
                    h2_elements = soup.find_all('h2')
                    for element in h2_elements:
                        text = self.clean_text(element.get_text())
                        if text and len(text) > 1 and len(text.split()) <= 4:
                            job_data['company'] = text
                            break
                    
                    # If still not found, try strong elements
                    if job_data['company'] == 'Not specified':
                        strong_elements = soup.find_all('strong')
                        for element in strong_elements:
                            text = self.clean_text(element.get_text())
                            # Look for company-like text
                            if text and len(text) > 1 and len(text.split()) <= 4 and \
                               not any(ignore in text.lower() for ignore in ['job', 'title', 'position', 'role', 'posted', 'date']):
                                job_data['company'] = text
                                break
        
        return job_data
    
    def get_combined_text(self, job_data):
        """Combine all job data into single text for analysis"""
        text_parts = []
        
        for key in ['title', 'company', 'location', 'description', 'requirements', 'benefits']:
            if job_data.get(key):
                text_parts.append(job_data[key])
        
        if job_data.get('full_content') and not text_parts:
            # If no specific elements found, use full content
            return job_data['full_content']
        
        return ' '.join(text_parts) if text_parts else job_data.get('full_content', '')