# Norma Evaluation App

The Norma Evaluation App is an evaluation platform designed to assess AI agents on various metrics like semantic similarity, intent classification, and latency. It integrates automated and manual evaluation processes to ensure scalability and accuracy. Built with a modern tech stack, including Next.js, Firebase, LangChain, and OpenAI, it provides robust tools for evaluating AI performance.

## Features

- **Evaluation**: Combines automated metrics with manual reviews.
- **Automated Metrics**:
  - Semantic Similarity
  - Intent Classification
  - Latency Checks
  - More ...
- **Manual Review UI**: Stakeholders can review and provide feedback on flagged cases.
- **Report Generation**: Downloadable evaluation reports in PDF and Excel formats.
- **Authentication**: Secure login with Firebase or Auth0.
- **Cloud Storage**: Secure file handling with Firebase Storage.

## Technology Stack

### Frontend

- **Framework**: [Next.js](https://nextjs.org)
- **UI Components**: ReactJS
- **Styling**: Tailwind CSS

### Backend

- **Evaluation Tools**: LangChain, OpenAI API
- **Hosting**: Google Cloud Run

### Database

- **Firestore**: Cloud-hosted NoSQL database
- **Secret Management**: Google Secret Manager

### DevOps

- **Source Control**: GitHub
- **CI/CD**: GitHub Actions

## Getting Started

### Prerequisites

- Node.js version 20+
- Firebase account with Firestore and Firebase Storage enabled
- Google Cloud account for Cloud Run and Secret Manager setup

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/norma-evaluation-app.git
   cd norma-evaluation-app
   ```
2. Install dependencies:

   ```bash
   npm install
   ```

3. Set up Firebase configuration in `.env.local`:
   ```env
   NEXT_PUBLIC_FIREBASE_API_KEY=<your_api_key>
   NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=<your_auth_domain>
   NEXT_PUBLIC_FIREBASE_PROJECT_ID=<your_project_id>
   NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=<your_storage_bucket>
   NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=<your_messaging_sender_id>
   NEXT_PUBLIC_FIREBASE_APP_ID=<your_app_id>
   NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID=<your_measurement_id>
   NEXT_PUBLIC_API_SERVICE_URL=<your_API_SERVICE_URL>
   ```
4. Set up OpenAI credentials in Google Secret Manager or `.env.local`:
   ```env
   OPENAI_API_KEY=<your_openai_api_key>
   ```

### Development Server

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to access the application.

## Usage

### Workflow

1. Log in using Firebase authentication.
2. Create a project and add agents for evaluation.
3. Upload test cases or manually create them in the UI.
4. Initiate a hybrid evaluation with desired thresholds.
5. Review flagged cases in the manual review phase.
6. Generate and download evaluation reports.

## License

## Contact

For queries or support, contact [support@norma.dev](mailto:support@norma.dev).
