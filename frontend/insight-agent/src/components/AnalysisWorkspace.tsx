import { useState } from "react";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AppMode } from "@/pages/Index";
import { ModeBadge } from "@/components/ModeBadge";
import { TeamOverview } from "@/components/TeamOverview";
import { StockSelector } from "@/components/StockSelector";
import { TimeWindowControls } from "@/components/TimeWindowControls";
import { GenerateSection } from "@/components/GenerateSection";
import { ResultsDisplay } from "@/components/ResultsDisplay";
import { apiClient, type Recommendation } from "@/lib/api";

interface AnalysisWorkspaceProps {
  mode: Exclude<AppMode, null>;
  onBackToModeSelection: () => void;
}

export const AnalysisWorkspace = ({ mode, onBackToModeSelection }: AnalysisWorkspaceProps) => {
  const [selectedTicker, setSelectedTicker] = useState<string>("");
  const [selectedRecommendation, setSelectedRecommendation] = useState<Recommendation | null>(null);
  const [fundWindow, setFundWindow] = useState(30);
  const [newsWindow, setNewsWindow] = useState(7);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<any>(null);

  const handleGenerate = async () => {
    if (!selectedRecommendation) return;

    setIsLoading(true);
    setResults(null);

    try {
      if (mode === "explainer") {
        // Start explainer job
        const { job_id } = await apiClient.runExplainer({
          rec_index: selectedRecommendation.index,
          fund_window_days: fundWindow,
          news_window_days: newsWindow,
        });

        // Poll for results
        const status = await apiClient.pollJobStatus(job_id, "explainer");
        
        if (status.result) {
          setResults(status.result);
        } else {
          throw new Error(status.error || "Unknown error");
        }
      } else {
        // Start recommender job
        const { job_id } = await apiClient.runRecommender({
          rec_index: selectedRecommendation.index,
          news_window_days: newsWindow,
          ticker: selectedRecommendation.ticker,
          company: selectedRecommendation.company,
        });

        // Poll for results
        const status = await apiClient.pollJobStatus(job_id, "recommender");
        
        if (status.result) {
          setResults(status.result);
        } else {
          throw new Error(status.error || "Unknown error");
        }
      }
    } catch (error) {
      console.error("Error generating analysis:", error);
      alert(`Error: ${error instanceof Error ? error.message : "Failed to generate analysis"}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      <header className="border-b-2 border-border/30 bg-card/80 backdrop-blur-md sticky top-0 z-10 shadow-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between max-w-7xl">
          <Button 
            variant="ghost" 
            onClick={onBackToModeSelection}
            className="gap-2 hover:bg-muted/50 transition-all duration-300 rounded-xl"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="font-medium">Back to Mode Selection</span>
          </Button>
          <ModeBadge mode={mode} />
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <TeamOverview mode={mode} />
        
        <div className="grid lg:grid-cols-3 gap-8 mb-8">
          <div className="lg:col-span-2 space-y-6">
            <StockSelector 
              mode={mode}
              selectedTicker={selectedTicker}
              onTickerChange={setSelectedTicker}
              selectedRecommendation={selectedRecommendation}
              onRecommendationChange={setSelectedRecommendation}
            />
            
            <TimeWindowControls
              fundWindow={fundWindow}
              newsWindow={newsWindow}
              onFundWindowChange={setFundWindow}
              onNewsWindowChange={setNewsWindow}
            />
          </div>

          <div className="lg:col-span-1">
            <GenerateSection
              mode={mode}
              disabled={!selectedTicker || !selectedRecommendation}
              isLoading={isLoading}
              onGenerate={handleGenerate}
            />
          </div>
        </div>

        {(isLoading || results) && (
          <ResultsDisplay
            mode={mode}
            isLoading={isLoading}
            results={results}
          />
        )}
      </div>
    </div>
  );
};
