type Project = {
  id: string; // Unique identifier for the project
  name: string; // Name of the project
  description: string; // Brief description of the project
  createdBy: string; // User ID of the project creator
  createdAt: Date; // Timestamp of creation
  updatedAt: Date; // Timestamp of last update
  status: "active" | "completed" | "archived";
};

type Agent = {
  id: string; // Unique identifier for the agent
  name: string; // Name of the agent
  projectId: string; // Reference to the project it belongs to
  endpointUrl: string; // API endpoint for the agent
  authDetails: {
    // Authentication details for accessing the agent
    type: "api_key" | "oauth";
    credentials: string;
  };
  createdAt: Date; // Timestamp of creation
  updatedAt: Date; // Timestamp of last update
  evaluationStatus: "pending" | "in_progress" | "completed"; // Current evaluation status
  evaluationMetrics: {
    // Aggregated metrics for the agent
    accuracy: number;
    relevance: number;
    safety: number;
    latency: number;
  };
};

type TestCase = {
  id: string; // Unique identifier for the test case
  projectId: string; // Reference to the project it belongs to
  input: string; // Query or input for the agent
  expectedOutput: string; // Ground truth response for comparison
  tags: string[]; // Tags for categorization
  createdBy: string; // User ID of the creator
  createdAt: Date; // Timestamp of creation
  updatedAt: Date; // Timestamp of last update
  status: "active" | "archived"; // Current status of the test case
};

type Evaluation = {
  id: string; // Unique identifier for the evaluation
  projectId: string; // Reference to the associated project
  agentId: string; // Reference to the evaluated agent
  status: "pending" | "in_progress" | "completed"; // Evaluation status
  startTime: Date; // Start time of the evaluation
  endTime: Date; // End time of the evaluation
  metrics: {
    // Aggregated metrics from evaluation
    accuracy: number;
    relevance: number;
    safety: number;
    latency: number;
  };
  results: {
    // Detailed results for each test case
    [testCaseId: string]: {
      input: string; // Input query
      agentResponse: string; // Agent's response
      expectedOutput: string; // Ground truth response
      metrics: {
        accuracy: number; // Accuracy score
        relevance: number; // Relevance score
        latency: number; // Response latency in ms
      };
      flagged: boolean; // Whether the response was flagged for manual review
    };
  };
};

type Feedback = {
  id: string; // Unique identifier for the feedback
  evaluationId: string; // Reference to the associated evaluation
  testCaseId: string; // Reference to the flagged test case
  correctedResponse: string; // Corrected response provided by the user
  feedback: {
    // Manual ratings provided by the user
    accuracy: number; // Accuracy score
    relevance: number; // Relevance score
    tone: "neutral" | "formal" | "friendly"; // Tone rating
    safetyFlag: boolean; // Whether the response is unsafe
  };
  createdBy: string; // User ID of the reviewer
  createdAt: Date; // Timestamp of feedback creation
};

type Log = {
  id: string; // Unique identifier for the log entry
  projectId: string; // Reference to the associated project
  agentId: string; // Reference to the associated agent
  event: string; // Type of event (e.g., "evaluation_started")
  details: string; // Detailed description of the event
  timestamp: Date; // When the event occurred
  userId: string; // User ID who triggered the event (if applicable)
};

type User = {
  id: string; // Unique user ID
  name: string; // Full name of the user
  email: string; // Email address
  role: "admin" | "user"; // Role within the system
  createdAt: Date; // Timestamp of user creation
  lastLogin: Date; // Timestamp of the last login
};

type Thresholds = {
  accuracy: number; // Minimum acceptable accuracy score
  relevance: number; // Minimum acceptable relevance score
  latency: number; // Maximum acceptable response time (in ms)
  safety: boolean; // Whether safety violations should trigger flags
};

export type { Thresholds, Evaluation, Feedback, Log, User, Project,Agent };
