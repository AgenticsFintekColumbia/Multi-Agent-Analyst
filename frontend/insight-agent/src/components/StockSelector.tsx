import { useEffect, useState, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AppMode } from "@/pages/Index";
import { AlertCircle, Loader2 } from "lucide-react";
import { apiClient, type Recommendation } from "@/lib/api";
import { format, parseISO } from "date-fns";

interface StockSelectorProps {
  mode: Exclude<AppMode, null>;
  selectedTicker: string;
  onTickerChange: (ticker: string) => void;
  selectedRecommendation: Recommendation | null;
  onRecommendationChange: (rec: Recommendation | null) => void;
}

export const StockSelector = ({
  mode,
  selectedTicker,
  onTickerChange,
  selectedRecommendation,
  onRecommendationChange,
}: StockSelectorProps) => {
  const isRecommender = mode === "recommender";
  const [tickers, setTickers] = useState<string[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loadingTickers, setLoadingTickers] = useState(true);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  const [tickerError, setTickerError] = useState<string | null>(null);

  // Load tickers on mount
  useEffect(() => {
    const loadTickers = async () => {
      try {
        setLoadingTickers(true);
        setTickerError(null);
        const data = await apiClient.getTickers();
        console.log("Loaded tickers:", data);
        setTickers(data.tickers || []);
        if (data.default && !selectedTicker) {
          onTickerChange(data.default);
        }
      } catch (error) {
        console.error("Failed to load tickers:", error);
        const errorMessage = error instanceof Error ? error.message : "Failed to load tickers. Make sure backend is running on http://localhost:8000";
        setTickerError(errorMessage);
        setTickers([]);
      } finally {
        setLoadingTickers(false);
      }
    };
    loadTickers();
  }, []);

  // Load recommendations when ticker changes
  useEffect(() => {
    if (!selectedTicker) {
      setRecommendations([]);
      onRecommendationChange(null);
      return;
    }

    const loadRecommendations = async () => {
      try {
        setLoadingRecommendations(true);
        const data = await apiClient.getRecommendations(selectedTicker, mode);
        setRecommendations(data.recommendations);
        onRecommendationChange(null); // Reset selection
      } catch (error) {
        console.error("Failed to load recommendations:", error);
      } finally {
        setLoadingRecommendations(false);
      }
    };
    loadRecommendations();
  }, [selectedTicker, mode]);

  // Group recommendations by year for both modes
  const recommendationsByYear = useMemo(() => {
    if (!recommendations.length) return {};
    
    const grouped: Record<string, Recommendation[]> = {};
    
    recommendations.forEach((rec) => {
      if (!rec.date) return;
      
      try {
        const date = parseISO(rec.date);
        const year = date.getFullYear().toString();
        
        if (!grouped[year]) {
          grouped[year] = [];
        }
        grouped[year].push(rec);
      } catch {
        // Skip invalid dates
      }
    });
    
    // Sort years descending (newest first) and sort recommendations within each year by date (newest first)
    const sortedGroups: Record<string, Recommendation[]> = {};
    Object.keys(grouped)
      .sort((a, b) => parseInt(b) - parseInt(a))
      .forEach((year) => {
        sortedGroups[year] = grouped[year].sort((a, b) => {
          if (!a.date || !b.date) return 0;
          try {
            const dateA = parseISO(a.date);
            const dateB = parseISO(b.date);
            return dateB.getTime() - dateA.getTime();
          } catch {
            return 0;
          }
        });
      });
    
    return sortedGroups;
  }, [recommendations]);

  return (
    <Card className="p-6 space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Stock Selection</h3>
        
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Ticker</label>
            <Select value={selectedTicker} onValueChange={onTickerChange} disabled={loadingTickers || tickers.length === 0}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder={loadingTickers ? "Loading tickers..." : tickers.length === 0 ? "No tickers available" : "Select a ticker..."} />
              </SelectTrigger>
              <SelectContent>
                {tickers.length === 0 ? (
                  <div className="px-2 py-6 text-center text-sm text-muted-foreground">
                    {tickerError ? (
                      <div>
                        <p className="font-medium text-destructive mb-1">Error loading tickers</p>
                        <p className="text-xs">{tickerError}</p>
                        <p className="text-xs mt-2">Check that backend is running on http://localhost:8000</p>
                      </div>
                    ) : (
                      "No tickers available"
                    )}
                  </div>
                ) : (
                  tickers.map((ticker) => (
                    <SelectItem key={ticker} value={ticker}>
                      {ticker}
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
            {tickerError && (
              <p className="text-xs text-destructive mt-1">{tickerError}</p>
            )}
          </div>

          {selectedTicker && (
            <div>
              <label className="text-sm font-medium mb-2 block">
                Recommendation
              </label>
              {isRecommender && (
                <div className="mb-2 flex items-start gap-2 p-3 rounded-lg bg-warning/10 border border-warning/20">
                  <AlertCircle className="w-4 h-4 text-warning mt-0.5 flex-shrink-0" />
                  <p className="text-xs text-warning">
                    Human rating is hidden to prevent model bias
                  </p>
                </div>
              )}
              <Select
                value={selectedRecommendation?.index?.toString()}
                onValueChange={(val) => {
                  const rec = recommendations.find(r => r.index.toString() === val);
                  onRecommendationChange(rec || null);
                }}
                disabled={loadingRecommendations}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder={loadingRecommendations ? (isRecommender ? "Loading dates..." : "Loading recommendations...") : (isRecommender ? "Select a date..." : "Select a recommendation...")} />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(recommendationsByYear).map(([year, recs]) => (
                    <SelectGroup key={year}>
                      <SelectLabel>{year}</SelectLabel>
                      {recs.map((rec) => {
                        if (!rec.date) return null;
                        try {
                          const date = parseISO(rec.date);
                          const formattedDate = format(date, "MMMM d");
                          // For explainer: show date + rating, for recommender: show only date
                          const displayText = isRecommender 
                            ? formattedDate
                            : `${formattedDate} - ${rec.rating || "N/A"}`;
                          return (
                            <SelectItem key={rec.index} value={rec.index.toString()}>
                              {displayText}
                            </SelectItem>
                          );
                        } catch {
                          return null;
                        }
                      })}
                    </SelectGroup>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>
      </div>

      {selectedRecommendation && (
        <div className="pt-4 border-t border-border">
          <h4 className="text-sm font-medium mb-3">Recommendation Details</h4>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-lg bg-muted/30">
              <p className="text-xs text-muted-foreground mb-1">Ticker</p>
              <p className="font-semibold">{selectedTicker}</p>
            </div>
            <div className="p-3 rounded-lg bg-muted/30">
              <p className="text-xs text-muted-foreground mb-1">Company</p>
              <p className="font-semibold">{selectedRecommendation.company || "N/A"}</p>
            </div>
            <div className="p-3 rounded-lg bg-muted/30">
              <p className="text-xs text-muted-foreground mb-1">Date</p>
              <p className="font-semibold">{selectedRecommendation.date || "N/A"}</p>
            </div>
            {!isRecommender && (
              <div className="p-3 rounded-lg bg-muted/30">
                <p className="text-xs text-muted-foreground mb-1">Rating</p>
                <p className="font-semibold">{selectedRecommendation.rating || "N/A"}</p>
              </div>
            )}
            <div className="p-3 rounded-lg bg-muted/30">
              <p className="text-xs text-muted-foreground mb-1">Analyst</p>
              <p className="font-semibold">{selectedRecommendation.analyst || "N/A"}</p>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
};
