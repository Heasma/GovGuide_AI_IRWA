// ============================================================
// GovGuide AI — Centralized Demonstration / Mock Data Architecture
// Clearly marked as demonstration data until real dataset integration.
// ============================================================

export const mockServices = [
  {
    id: 'srv-001',
    name: 'National Identity Card (NIC) Application',
    category: 'Citizen Services',
    department: 'Department of Registration of Persons',
    description: 'Apply for a new National Identity Card or request a renewal / replacement for lost or damaged cards.',
    status: 'Online Available',
    processingTime: '5-10 Working Days',
    fee: 'LKR 500',
    eligibility: 'Citizens aged 15 years and above residing in Sri Lanka.',
    documentsRequired: ['Birth Certificate', 'Gramasewaka Certificate', 'Passport Photo (ICAO standard)'],
    onlineLink: 'https://nic.gov.lk'
  },
  {
    id: 'srv-002',
    name: 'Passport Issuance & Renewal',
    category: 'Citizen Services',
    department: 'Department of Immigration & Emigration',
    description: 'Schedule appointments, submit applications for all-country passports, and track delivery status.',
    status: 'Online Appointment',
    processingTime: '1-3 Working Days (Urgent) / 14 Days (Normal)',
    fee: 'LKR 5,000 - 20,000',
    eligibility: 'Sri Lankan citizens holding valid NIC and birth registration.',
    documentsRequired: ['Original Birth Certificate', 'Original NIC', 'Dual Citizenship Certificate (if applicable)'],
    onlineLink: 'https://immigration.gov.lk'
  },
  {
    id: 'srv-003',
    name: 'Driving License Renewal & Duplicate',
    category: 'Transport',
    department: 'Department of Motor Traffic',
    description: 'Renew light and heavy vehicle driving licenses or request duplicates for damaged permits online.',
    status: 'Online Available',
    processingTime: '3-5 Working Days',
    fee: 'LKR 2,500',
    eligibility: 'Current Sri Lankan driving license holders with valid NTMI medical report.',
    documentsRequired: ['NTMI Medical Certificate', 'Current Driving License', 'NIC Copy'],
    onlineLink: 'https://dmt.gov.lk'
  },
  {
    id: 'srv-004',
    name: 'Business Name Registration (Sole Proprietorship)',
    category: 'Business Services',
    department: 'Department of Registrar of Companies',
    description: 'Register new sole proprietorships or partnerships with Provincial Registrar of Companies.',
    status: 'Online Available',
    processingTime: '2-4 Working Days',
    fee: 'LKR 2,000',
    eligibility: 'Sri Lankan residents operating commercial activities within provincial boundaries.',
    documentsRequired: ['Draft Business Name Inquiry Form', 'NIC Copies of Owners', 'Address Verification'],
    onlineLink: 'https://e-drc.gov.lk'
  },
  {
    id: 'srv-005',
    name: 'Taxpayer Identification Number (TIN) Registration',
    category: 'Tax & Revenue',
    department: 'Inland Revenue Department',
    description: 'Obtain mandatory Taxpayer Identification Number (TIN) for individuals and corporate entities.',
    status: 'Fully Digital',
    processingTime: '1-2 Working Days',
    fee: 'Free of Charge',
    eligibility: 'All individuals aged 18+ and registered corporate businesses.',
    documentsRequired: ['NIC or Passport Copy', 'Proof of Business Address'],
    onlineLink: 'https://ird.gov.lk'
  },
  {
    id: 'srv-006',
    name: 'Birth, Marriage & Death Certificate Copies',
    category: 'Citizen Services',
    department: 'Registrar General\'s Department',
    description: 'Request official certified copies of civil status certificates registered across all divisions.',
    status: 'Online Order & Delivery',
    processingTime: '3-7 Working Days',
    fee: 'LKR 200 per copy',
    eligibility: 'Immediate family members or legally authorized representatives.',
    documentsRequired: ['Registration Number / Entry Details', 'Applicant NIC'],
    onlineLink: 'https://rgd.gov.lk'
  },
  {
    id: 'srv-007',
    name: 'Senior Citizen Pension Support & Social Allowance',
    category: 'Social Services',
    department: 'Department of Social Services',
    description: 'Enroll in monthly financial assistance and healthcare benefit programs for senior citizens.',
    status: 'In-Person & Portal',
    processingTime: '14-21 Working Days',
    fee: 'Free of Charge',
    eligibility: 'Sri Lankan citizens aged 70+ meeting household income criteria.',
    documentsRequired: ['NIC Copy', 'Samurdhi / Household Income Certificate', 'Bank Passbook Copy'],
    onlineLink: 'https://socialservices.gov.lk'
  },
  {
    id: 'srv-008',
    name: 'G.C.E. O/L & A/L Certificate Verification',
    category: 'Education',
    department: 'Department of Examinations',
    description: 'Request official academic result verification letters dispatched directly to foreign universities or employers.',
    status: 'Fully Digital',
    processingTime: '2-5 Working Days',
    fee: 'LKR 1,500',
    eligibility: 'Candidates who appeared for G.C.E. Ordinary or Advanced Level examinations.',
    documentsRequired: ['Index Number', 'Year of Examination', 'Recipient Institution Details'],
    onlineLink: 'https://doenets.lk'
  }
];

export const mockDepartments = [
  {
    id: 'dept-001',
    name: 'Department of Immigration & Emigration',
    code: 'DIE',
    serviceCount: 14,
    location: 'Suhurupaya, Battaramulla',
    contact: '+94 11 210 1500',
    email: 'info@immigration.gov.lk',
    website: 'https://immigration.gov.lk',
    description: 'Responsible for border security, travel documentation, visa issuance, and citizenship services.'
  },
  {
    id: 'dept-002',
    name: 'Department of Motor Traffic',
    code: 'DMT',
    serviceCount: 22,
    location: 'Elwitigala Mawatha, Colombo 05',
    contact: '+94 11 269 4331',
    email: 'info@dmt.gov.lk',
    website: 'https://dmt.gov.lk',
    description: 'Regulates motor vehicles, driving licenses, vehicle registrations, and road transport compliance.'
  },
  {
    id: 'dept-003',
    name: 'Department of Registration of Persons',
    code: 'DRP',
    serviceCount: 8,
    location: 'Suhurupaya, Battaramulla',
    contact: '+94 11 522 6100',
    email: 'info@drp.gov.lk',
    website: 'https://drp.gov.lk',
    description: 'Issues National Identity Cards and manages civil identification registry data for citizens.'
  },
  {
    id: 'dept-004',
    name: 'Inland Revenue Department',
    code: 'IRD',
    serviceCount: 19,
    location: 'Sir Chittampalam A. Gardiner Mawatha, Colombo 02',
    contact: '+94 11 213 5000',
    email: 'taxinfo@ird.gov.lk',
    website: 'https://ird.gov.lk',
    description: 'Manages national tax collection, TIN issuance, VAT/RAMIS services, and revenue compliance.'
  },
  {
    id: 'dept-005',
    name: 'Registrar General\'s Department',
    code: 'RGD',
    serviceCount: 16,
    location: 'Nawam Mawatha, Colombo 02',
    contact: '+94 11 288 9500',
    email: 'info@rgd.gov.lk',
    website: 'https://rgd.gov.lk',
    description: 'Maintains national registries for births, marriages, deaths, and land registrations.'
  },
  {
    id: 'dept-006',
    name: 'Department of Social Services',
    code: 'DSS',
    serviceCount: 11,
    location: 'Sethsiripaya, Battaramulla',
    contact: '+94 11 287 4930',
    email: 'info@socialservices.gov.lk',
    website: 'https://socialservices.gov.lk',
    description: 'Provides social welfare assistance, disability support, and elderly care programs.'
  }
];

export const mockOffices = [
  {
    id: 'off-001',
    name: 'Head Office - Suhurupaya Passport Complex',
    department: 'Department of Immigration & Emigration',
    district: 'Colombo / Gampaha',
    location: 'Suhurupaya, Subhuthipura Road, Battaramulla',
    contact: '+94 11 210 1500',
    hours: 'Mon - Fri: 8:00 AM - 4:30 PM',
    servicesAvailable: ['Passports', 'Dual Citizenship', 'Visas', 'Emergency Certificates']
  },
  {
    id: 'off-002',
    name: 'Werahera Motor Traffic Branch',
    department: 'Department of Motor Traffic',
    district: 'Colombo / Kalutara',
    location: 'Werahera, Boralesgamuwa',
    contact: '+94 11 251 8920',
    hours: 'Mon - Fri: 8:30 AM - 4:00 PM',
    servicesAvailable: ['Driving License Renewal', 'Medical Examinations', 'Trial Appointments']
  },
  {
    id: 'off-003',
    name: 'Kandy Regional Passport Office',
    department: 'Department of Immigration & Emigration',
    district: 'Kandy',
    location: 'No 42, Sangamitta Mawatha, Kandy',
    contact: '+94 81 222 2341',
    hours: 'Mon - Fri: 8:00 AM - 3:30 PM',
    servicesAvailable: ['All-Country Passport Applications', 'Renewal Services']
  },
  {
    id: 'off-004',
    name: 'Galle Provincial Registrar Office',
    department: 'Registrar General\'s Department',
    district: 'Galle',
    location: 'Fort Secretariat, Galle',
    contact: '+94 91 223 4102',
    hours: 'Mon - Fri: 8:30 AM - 4:15 PM',
    servicesAvailable: ['Birth/Marriage Certificate Copies', 'Land Deed Extracts']
  },
  {
    id: 'off-005',
    name: 'Jaffna Inland Revenue Regional Office',
    department: 'Inland Revenue Department',
    district: 'Jaffna',
    location: 'Kankesanthurai Road, Jaffna',
    contact: '+94 21 222 5104',
    hours: 'Mon - Fri: 8:30 AM - 4:15 PM',
    servicesAvailable: ['TIN Issuance', 'Tax Advisory', 'RAMIS Assistance']
  }
];

export const mockDocuments = [
  {
    id: 'doc-001',
    title: 'Imm & Emig Act No. 20 - Regulations & Amendment 2024',
    department: 'Department of Immigration & Emigration',
    type: 'Gazette / Legal Act',
    publishedDate: '2024-03-15',
    verificationStatus: 'Verified',
    fileSize: '2.4 MB',
    language: 'English / Sinhala'
  },
  {
    id: 'doc-002',
    title: 'Motor Traffic Act Guidelines on E-License Renewal',
    department: 'Department of Motor Traffic',
    type: 'Official Circular',
    publishedDate: '2024-01-10',
    verificationStatus: 'Verified',
    fileSize: '1.1 MB',
    language: 'English'
  },
  {
    id: 'doc-003',
    title: 'Inland Revenue Circular on Individual TIN Mandatory Registration',
    department: 'Inland Revenue Department',
    type: 'Tax Guidelines',
    publishedDate: '2023-11-28',
    verificationStatus: 'Verified',
    fileSize: '850 KB',
    language: 'English / Tamil'
  },
  {
    id: 'doc-004',
    title: 'Standard Operating Procedure for Senior Citizen Allowances 2024',
    department: 'Department of Social Services',
    type: 'Policy Document',
    publishedDate: '2024-02-01',
    verificationStatus: 'Pending Verification',
    fileSize: '3.8 MB',
    language: 'Sinhala / English'
  },
  {
    id: 'doc-005',
    title: 'Registrar General Guide to Consular Certificate Applications',
    department: 'Registrar General\'s Department',
    type: 'Public Manual',
    publishedDate: '2023-09-14',
    verificationStatus: 'Verified',
    fileSize: '1.9 MB',
    language: 'English'
  }
];

export const mockKnowledgeSources = [
  {
    id: 'src-001',
    name: 'Department of Immigration Official Web Portal',
    url: 'https://immigration.gov.lk',
    type: 'Government Website',
    documentCount: 142,
    lastUpdated: '2026-08-01',
    verificationStatus: 'Verified',
    reliabilityScore: '99.4%'
  },
  {
    id: 'src-002',
    name: 'Government Gazette Archive (1998 - 2026)',
    url: 'https://documents.gov.lk',
    type: 'Official Portal',
    documentCount: 1240,
    lastUpdated: '2026-08-10',
    verificationStatus: 'Verified',
    reliabilityScore: '100%'
  },
  {
    id: 'src-003',
    name: 'Motor Traffic e-Services Registry',
    url: 'https://dmt.gov.lk',
    type: 'Government Portal',
    documentCount: 88,
    lastUpdated: '2026-07-25',
    verificationStatus: 'Verified',
    reliabilityScore: '98.1%'
  },
  {
    id: 'src-004',
    name: 'Inland Revenue Tax Knowledge Base',
    url: 'https://ird.gov.lk/kb',
    type: 'Public Information',
    documentCount: 215,
    lastUpdated: '2026-08-05',
    verificationStatus: 'Pending Verification',
    reliabilityScore: '94.5%'
  }
];

export const mockConversations = [
  {
    id: 'conv-001',
    title: 'Passport Renewal Required Documents & Fees',
    timestamp: '2026-08-13 14:20',
    messageCount: 6,
    lastMessage: 'The fee for one-day urgent passport renewal is LKR 20,000 at Suhurupaya.',
    status: 'Completed',
    queryTopic: 'Passport Services'
  },
  {
    id: 'conv-002',
    title: 'Individual TIN Registration Eligibility Query',
    timestamp: '2026-08-12 09:45',
    messageCount: 4,
    lastMessage: 'All Sri Lankan residents aged 18 and above require a TIN number.',
    status: 'Completed',
    queryTopic: 'Tax & Revenue'
  },
  {
    id: 'conv-003',
    title: 'Driving License Medical Test Renewal Requirements',
    timestamp: '2026-08-11 16:10',
    messageCount: 8,
    lastMessage: 'NTMI medical reports remain valid for 6 months from issue date.',
    status: 'Completed',
    queryTopic: 'Driving License'
  },
  {
    id: 'conv-004',
    title: 'Senior Citizen Health Card Application Process',
    timestamp: '2026-08-10 11:30',
    messageCount: 5,
    lastMessage: 'Applications must be endorsed by your Divisional Secretariat office.',
    status: 'Completed',
    queryTopic: 'Social Services'
  }
];

export const mockSearchHistory = [
  {
    id: 'sh-001',
    query: 'NIC replacement application fee 2026',
    timestamp: '2026-08-13 18:14',
    resultCount: 12,
    category: 'Citizen Services',
    status: 'Success'
  },
  {
    id: 'sh-002',
    query: 'Immigration passport urgent appointment Werahera',
    timestamp: '2026-08-13 15:02',
    resultCount: 8,
    category: 'Citizen Services',
    status: 'Success'
  },
  {
    id: 'sh-003',
    query: 'Sole proprietorship business registration provincial tax',
    timestamp: '2026-08-12 11:40',
    resultCount: 15,
    category: 'Business Services',
    status: 'Success'
  },
  {
    id: 'sh-004',
    query: 'GCE Advanced Level exam results verification letter online',
    timestamp: '2026-08-11 09:22',
    resultCount: 6,
    category: 'Education',
    status: 'Success'
  }
];

export const mockDashboardStats = {
  servicesCount: 128,
  officesCount: 45,
  knowledgeSourcesCount: 14,
  documentsCount: 1680,
  recentActivity: [
    { id: 'act-1', type: 'Service Search', item: 'NIC Application Fee Query', user: 'demo@gmail.com', time: '10 mins ago', status: 'Completed' },
    { id: 'act-2', type: 'AI Conversation', item: 'Passport Renewal Documents', user: 'demo@gmail.com', time: '45 mins ago', status: 'Completed' },
    { id: 'act-3', type: 'Document Retrieval', item: 'Motor Traffic Act Circular 2024', user: 'system', time: '2 hours ago', status: 'Completed' },
    { id: 'act-4', type: 'Source Check', item: 'IRD Tax Portal Indexing', user: 'system', time: '4 hours ago', status: 'Processing' },
    { id: 'act-5', type: 'Dataset Sync', item: 'Gov Services Master Schema', user: 'admin', time: 'Yesterday', status: 'Pending' }
  ]
};

export const mockPipelineStages = [
  { stage: 'Data Source', status: 'Waiting for Dataset', description: 'Awaiting official government registry dataset export.', color: '#f59e0b' },
  { stage: 'Data Validation', status: 'Ready (Schema Configured)', description: 'Validation rules & schema parsers initialized.', color: '#3b82f6' },
  { stage: 'Preprocessing', status: 'Ready (NLP Pipeline)', description: 'spaCy / NLTK chunking & normalization engines ready.', color: '#3b82f6' },
  { stage: 'Indexing', status: 'Pending Dataset', description: 'pgvector & BM25 inverted index structures ready for ingestion.', color: '#f59e0b' },
  { stage: 'Knowledge Retrieval', status: 'Active (Stub / Demo Engine)', description: 'Hybrid research agent executing with fallback stub response.', color: '#10b981' }
];
