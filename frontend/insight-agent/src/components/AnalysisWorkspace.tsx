import { useState, useEffect } from "react";
import { ArrowLeft, Search, TrendingUp, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AppMode } from "@/pages/Index";
import { ModeBadge } from "@/components/ModeBadge";
import { TeamOverview } from "@/components/TeamOverview";
import { StockSelector } from "@/components/StockSelector";
import { TimeWindowControls } from "@/components/TimeWindowControls";
import { GenerateSection } from "@/components/GenerateSection";
import { ResultsDisplay } from "@/components/ResultsDisplay";
import { apiClient, type Recommendation, type Config } from "@/lib/api";

interface AnalysisWorkspaceProps {
  mode: Exclude<AppMode, null>;
  onBackToModeSelection: () => void;
}

export const AnalysisWorkspace = ({ mode, onBackToModeSelection }: AnalysisWorkspaceProps) => {
  const [selectedTicker, setSelectedTicker] = useState<string>("");
  const [selectedRecommendation, setSelectedRecommendation] = useState<Recommendation | null>(null);
  const [config, setConfig] = useState<Config | null>(null);
  const [fundWindow, setFundWindow] = useState<number>(90); // Default fallback, will be updated from backend
  const [newsWindow, setNewsWindow] = useState<number>(30); // Default fallback, will be updated from backend
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<any>(null);

  // Fetch config from backend on mount
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const configData = await apiClient.getConfig();
        setConfig(configData);
        // Set defaults from backend
        if (mode === "explainer") {
          setFundWindow(configData.defaults.explainer.fund_window_days);
          setNewsWindow(configData.defaults.explainer.news_window_days);
        } else {
          setNewsWindow(configData.defaults.recommender.news_window_days);
        }
      } catch (error) {
        console.error("Failed to load config:", error);
        // Keep default fallback values
      }
    };
    loadConfig();
  }, [mode]);

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
    <div className={`min-h-screen ${selectedTicker && selectedRecommendation ? "pb-24" : ""}`}>
      <header className="border-b border-border/50 bg-card/80 backdrop-blur-md sticky top-0 z-10 shadow-sm">
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

      <div className="container mx-auto px-4 py-8 max-w-7xl space-y-6">
        <TeamOverview mode={mode} />
        
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6 pb-8">
            <StockSelector 
              mode={mode}
              selectedTicker={selectedTicker}
              onTickerChange={setSelectedTicker}
              selectedRecommendation={selectedRecommendation}
              onRecommendationChange={setSelectedRecommendation}
            />
            
            <TimeWindowControls
              mode={mode}
              newsWindow={newsWindow}
              onNewsWindowChange={setNewsWindow}
              fundWindowDays={config?.defaults.explainer.fund_window_days}
              technicalWindowDays={config?.defaults.explainer.technical_window_days}
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

      {/* Sticky Bottom Action Bar */}
      {selectedTicker && selectedRecommendation && (
        <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-border/50 bg-card/95 backdrop-blur-md shadow-xl">
          <div className="container mx-auto px-4 py-4 max-w-7xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4 text-sm">
                <span className="font-semibold text-foreground">
                  Ticker: <span className="font-bold text-primary">{selectedTicker}</span>
                </span>
                <span className="text-muted-foreground">·</span>
                <span className="font-semibold text-foreground">
                  NEWS: <span className="font-bold text-success">{newsWindow}</span> days
                </span>
              </div>
              <Button
                onClick={handleGenerate}
                disabled={isLoading}
                className={`h-10 px-6 font-semibold rounded-lg shadow-md hover:shadow-lg transition-all duration-300 ${
                  mode === "explainer"
                    ? "bg-explainer hover:bg-explainer/90 text-white"
                    : "bg-recommender hover:bg-recommender/90 text-white"
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    {mode === "explainer" ? (
                      <>
                        <Search className="w-4 h-4 mr-2" />
                        <span>Generate Explanation</span>
                      </>
                    ) : (
                      <>
                        <TrendingUp className="w-4 h-4 mr-2" />
                        <span>Generate Recommendation</span>
                      </>
                    )}
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
