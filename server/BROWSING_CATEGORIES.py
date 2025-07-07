# update this to include sites you want to track!
BROWSING_CATEGORIES = { # update this to include sites you want to track
    'social_media': {
        'domains': [
            'facebook.com', 'twitter.com', 'x.com', 'instagram.com', 'reddit.com', 
            'linkedin.com', 'tiktok.com', 'snapchat.com', 'pinterest.com', 
            'tumblr.com', 'discord.com', 'slack.com', 'whatsapp.com', 'telegram.org',
            'mastodon.social', 'threads.net', 'bsky.social', 'bereal.com'
        ],
        'patterns': [r'social', r'/comments/', r'/status/', r'/post/'],
        'subcategories': {
            'professional': ['linkedin.com', 'slack.com'],
            'messaging': ['whatsapp.com', 'telegram.org', 'discord.com'],
            'content_sharing': ['instagram.com', 'tiktok.com', 'pinterest.com']
        }
    },
    
    'entertainment': {
        'domains': [
            'youtube.com', 'netflix.com', 'spotify.com', 'twitch.tv', 'hulu.com',
            'disneyplus.com', 'hbomax.com', 'primevideo.com', 'vimeo.com',
            'soundcloud.com', 'pandora.com', 'applemusic.com', 'deezer.com',
            'crunchyroll.com', 'funimation.com', 'steam.com', 'epicgames.com',
            'ign.com', 'gamespot.com', 'kotaku.com', 'polygon.com'
        ],
        'patterns': [r'/watch', r'/video/', r'/episode/', r'/game/', r'wiki\.fandom\.com'],
        'subcategories': {
            'video': ['youtube.com', 'netflix.com', 'twitch.tv'],
            'music': ['spotify.com', 'soundcloud.com', 'pandora.com'],
            'gaming': ['steam.com', 'epicgames.com', 'ign.com', r'\.fandom\.com']
        }
    },
    
    'development': {
        'domains': [
            'stackoverflow.com', 'github.com', 'gitlab.com', 'bitbucket.org',
            'developer.mozilla.org', 'w3schools.com', 'css-tricks.com',
            'dev.to', 'hashnode.dev', 'codesandbox.io', 'codepen.io',
            'jsfiddle.net', 'replit.com', 'vercel.com', 'netlify.com',
            'npmjs.com', 'pypi.org', 'crates.io', 'packagist.org',
            'docker.com', 'kubernetes.io', 'terraform.io'
        ],
        'patterns': [
            r'docs\..*\.(?:com|org|io)', r'.*\.readthedocs\.io', r'/documentation/',
            r'/api/', r'/reference/', r'github\.com/.*/(?:issues|pull|wiki)',
            r'stackoverflow\.com/questions/'
        ],
        'subcategories': {
            'q&a': ['stackoverflow.com', 'dev.to'],
            'repositories': ['github.com', 'gitlab.com', 'bitbucket.org'],
            'documentation': [r'docs\.', r'\.readthedocs\.io', 'developer.mozilla.org'],
            'tools': ['codesandbox.io', 'codepen.io', 'replit.com']
        }
    },
    
    'learning': {
        'domains': [
            'coursera.org', 'udemy.com', 'edx.org', 'khanacademy.org',
            'udacity.com', 'pluralsight.com', 'lynda.com', 'skillshare.com',
            'masterclass.com', 'brilliant.org', 'datacamp.com', 'codecademy.com',
            'freecodecamp.org', 'mit.edu', 'stanford.edu', 'harvard.edu',
            'arxiv.org', 'scholar.google.com', 'jstor.org', 'pubmed.ncbi.nlm.nih.gov',
            'wikipedia.org', 'wikihow.com', 'instructables.com'
        ],
        'patterns': [
            r'/course/', r'/tutorial/', r'/learn/', r'/guide/', r'/how-to',
            r'\.edu/', r'/research/', r'/paper/', r'/study/'
        ],
        'subcategories': {
            'moocs': ['coursera.org', 'udemy.com', 'edx.org'],
            'technical': ['freecodecamp.org', 'codecademy.com', 'datacamp.com'],
            'academic': ['arxiv.org', 'scholar.google.com', 'jstor.org', r'\.edu/'],
            'practical': ['wikihow.com', 'instructables.com']
        }
    },
    
    'productivity': {
        'domains': [
            'notion.so', 'trello.com', 'asana.com', 'todoist.com', 'monday.com',
            'clickup.com', 'airtable.com', 'basecamp.com', 'jira.atlassian.com',
            'confluence.atlassian.com', 'evernote.com', 'onenote.com', 'obsidian.md',
            'roamresearch.com', 'workflowy.com', 'calendar.google.com', 'outlook.com',
            'zoom.us', 'meet.google.com', 'teams.microsoft.com', 'calendly.com'
        ],
        'patterns': [r'/calendar/', r'/tasks/', r'/projects/', r'/workspace/'],
        'subcategories': {
            'project_management': ['trello.com', 'asana.com', 'jira.atlassian.com'],
            'notes': ['notion.so', 'evernote.com', 'obsidian.md'],
            'communication': ['zoom.us', 'meet.google.com', 'teams.microsoft.com']
        }
    },
    
    'news': {
        'domains': [
            'nytimes.com', 'washingtonpost.com', 'wsj.com', 'ft.com', 'economist.com',
            'bbc.com', 'cnn.com', 'reuters.com', 'apnews.com', 'npr.org',
            'theguardian.com', 'foxnews.com', 'nbcnews.com', 'abcnews.go.com',
            'usatoday.com', 'politico.com', 'axios.com', 'bloomberg.com',
            'techcrunch.com', 'theverge.com', 'arstechnica.com', 'wired.com',
            'hackernews.com', 'news.ycombinator.com', 'lobste.rs', 'slashdot.org'
        ],
        'patterns': [r'/article/', r'/story/', r'/news/', r'/\d{4}/\d{2}/\d{2}/'],
        'subcategories': {
            'mainstream': ['nytimes.com', 'bbc.com', 'cnn.com'],
            'tech': ['techcrunch.com', 'theverge.com', 'arstechnica.com'],
            'aggregators': ['news.ycombinator.com', 'reddit.com/r/news']
        }
    },
    
    'shopping': {
        'domains': [
            'amazon.com', 'ebay.com', 'etsy.com', 'alibaba.com', 'walmart.com',
            'target.com', 'bestbuy.com', 'homedepot.com', 'lowes.com', 'ikea.com',
            'wayfair.com', 'shopify.com', 'wish.com', 'costco.com', 'sephora.com',
            'ulta.com', 'nike.com', 'adidas.com', 'apple.com', 'samsung.com'
        ],
        'patterns': [r'/product/', r'/cart/', r'/checkout/', r'/shop/', r'/store/'],
        'subcategories': {
            'marketplace': ['amazon.com', 'ebay.com', 'etsy.com'],
            'retail': ['walmart.com', 'target.com', 'costco.com'],
            'specialty': ['sephora.com', 'nike.com', 'apple.com']
        }
    },
    
    'finance': {
        'domains': [
            'chase.com', 'bankofamerica.com', 'wellsfargo.com', 'citi.com',
            'paypal.com', 'venmo.com', 'cashapp.com', 'zelle.com', 'wise.com',
            'coinbase.com', 'binance.com', 'kraken.com', 'robinhood.com',
            'etrade.com', 'fidelity.com', 'vanguard.com', 'schwab.com',
            'mint.com', 'ynab.com', 'personalcapital.com', 'creditkarma.com'
        ],
        'patterns': [r'/banking/', r'/wallet/', r'/account/', r'/trading/'],
        'subcategories': {
            'banking': ['chase.com', 'bankofamerica.com', 'wellsfargo.com'],
            'payments': ['paypal.com', 'venmo.com', 'cashapp.com'],
            'investing': ['robinhood.com', 'fidelity.com', 'vanguard.com'],
            'crypto': ['coinbase.com', 'binance.com', 'kraken.com']
        }
    },
    
    'health': {
        'domains': [
            'webmd.com', 'mayoclinic.org', 'healthline.com', 'medlineplus.gov',
            'nih.gov', 'cdc.gov', 'who.int', 'drugs.com', 'rxlist.com',
            'myfitnesspal.com', 'fitbit.com', 'strava.com', 'headspace.com',
            'calm.com', 'betterhelp.com', 'talkspace.com', 'zocdoc.com'
        ],
        'patterns': [r'/health/', r'/medical/', r'/symptoms/', r'/conditions/'],
        'subcategories': {
            'medical_info': ['webmd.com', 'mayoclinic.org', 'healthline.com'],
            'fitness': ['myfitnesspal.com', 'fitbit.com', 'strava.com'],
            'mental_health': ['headspace.com', 'calm.com', 'betterhelp.com']
        }
    },
    
    'reference': {
        'domains': [
            'google.com', 'bing.com', 'duckduckgo.com', 'yandex.com', 'baidu.com',
            'dictionary.com', 'thesaurus.com', 'merriam-webster.com', 'oxforddictionaries.com',
            'translate.google.com', 'deepl.com', 'wolframalpha.com', 'archive.org',
            'maps.google.com', 'openstreetmap.org', 'waze.com', 'weather.com',
            'timeanddate.com', 'xe.com', 'calculator.net'
        ],
        'patterns': [r'/search', r'/define/', r'/translate/', r'/maps/', r'/directions/'],
        'subcategories': {
            'search': ['google.com', 'bing.com', 'duckduckgo.com'],
            'language': ['dictionary.com', 'translate.google.com', 'deepl.com'],
            'utilities': ['maps.google.com', 'weather.com', 'xe.com']
        }
    },
    
    'professional': {
        'domains': [
            'salesforce.com', 'hubspot.com', 'zendesk.com', 'intercom.com',
            'mailchimp.com', 'constantcontact.com', 'hootsuite.com', 'buffer.com',
            'canva.com', 'figma.com', 'adobe.com', 'sketch.com', 'miro.com',
            'tableau.com', 'powerbi.microsoft.com', 'datastudio.google.com'
        ],
        'patterns': [r'/dashboard/', r'/analytics/', r'/reports/', r'/design/'],
        'subcategories': {
            'crm': ['salesforce.com', 'hubspot.com', 'zendesk.com'],
            'marketing': ['mailchimp.com', 'hootsuite.com', 'buffer.com'],
            'design': ['canva.com', 'figma.com', 'adobe.com'],
            'analytics': ['tableau.com', 'powerbi.microsoft.com']
        }
    }
}