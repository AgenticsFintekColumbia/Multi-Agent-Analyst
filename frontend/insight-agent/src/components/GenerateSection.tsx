import { Search, TrendingUp, Loader2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AppMode } from "@/pages/Index";

interface GenerateSectionProps {
  mode: Exclude<AppMode, null>;
  disabled: boolean;
  isLoading: boolean;
  onGenerate: () => void;
}

export const GenerateSection = ({ mode, disabled, isLoading, onGenerate }: GenerateSectionProps) => {
  const isExplainer = mode === "explainer";
  
  return (
    <Card className={`p-8 sticky top-24 border-2 ${
      isExplainer 
        ? "border-explainer/30 bg-gradient-to-br from-card via-explainer/5 to-card" 
        : "border-recommender/30 bg-gradient-to-br from-card via-recommender/5 to-card"
    } relative overflow-hidden`}>
      <div className={`absolute top-0 right-0 w-40 h-40 rounded-full blur-3xl opacity-20 ${
        isExplainer ? "bg-explainer" : "bg-recommender"
      }`} />
      <div className="relative space-y-6">
        <div>
          <h3 className="text-2xl font-black mb-3 bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
            Generate Analysis
          </h3>
          <p className="text-sm text-foreground/80 leading-relaxed">
            {isExplainer 
              ? "Run the explainer team to understand the analyst's rating rationale" 
              : "Run the recommender team to generate an independent model rating"}
          </p>
        </div>

        <Button
          onClick={onGenerate}
          disabled={disabled || isLoading}
          className={`w-full h-14 text-lg font-bold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 ${
            isExplainer
              ? "bg-gradient-to-r from-explainer to-explainer/80 hover:from-explainer/90 hover:to-explainer/70 text-white"
              : "bg-gradient-to-r from-recommender to-recommender/80 hover:from-recommender/90 hover:to-recommender/70 text-white"
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {isLoading ? (
            <>
              <Loader2 className="w-6 h-6 mr-3 animate-spin" />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              {isExplainer ? (
                <Search className="w-6 h-6 mr-3" />
              ) : (
                <TrendingUp className="w-6 h-6 mr-3" />
              )}
              <span>Run {isExplainer ? "Explainer" : "Recommender"} Team</span>
            </>
          )}
        </Button>

        {isLoading && (
          <div className="space-y-4 p-4 rounded-xl bg-muted/30 border border-border/50">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground font-medium">Estimated time:</span>
              <span className="font-bold text-foreground">{isExplainer ? "30-60s" : "60-90s"}</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div className={`h-full bg-gradient-to-r ${
                isExplainer 
                  ? "from-explainer to-explainer/70" 
                  : "from-recommender to-recommender/70"
              } animate-pulse rounded-full`} style={{ width: "60%" }} />
            </div>
            <p className="text-xs text-muted-foreground text-center font-mono">
              {isExplainer ? "Manager is collecting reports from the 3 analysts..." : "Manager is aggregating analyst views..."}
            </p>
          </div>
        )}
      </div>
    </Card>
  );
};
