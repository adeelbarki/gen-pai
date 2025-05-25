export interface ChatResponse {
  answer: string;
  results: { name: string; description: string; score: number }[];
}
