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
    <Card className={`p-8 sticky top-24 border border-border/50 bg-card/80 backdrop-blur-sm ${
      isExplainer 
        ? "border-explainer/20" 
        : "border-recommender/20"
    } relative overflow-hidden`}>
      <div className={`absolute top-0 right-0 w-40 h-40 rounded-full blur-3xl opacity-20 ${
        isExplainer ? "bg-explainer" : "bg-recommender"
      }`} />
      <div className="relative space-y-6">
        <div>
          <h3 className="text-lg font-semibold mb-3 tracking-tight text-foreground">
            Generate Analysis
          </h3>
          <p className="text-sm text-foreground/70 leading-relaxed">
            {isExplainer 
              ? "Generate an explanation for the analyst's rating rationale" 
              : "Generate an independent model rating based on multi-agent analysis"}
          </p>
        </div>

        <Button
          onClick={onGenerate}
          disabled={disabled || isLoading}
          className={`w-full h-12 text-base font-semibold rounded-lg shadow-md hover:shadow-lg transition-all duration-300 ${
            isExplainer
              ? "bg-explainer hover:bg-explainer/90 text-white"
              : "bg-recommender hover:bg-recommender/90 text-white"
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
              <span>Generate {isExplainer ? "Explanation" : "Recommendation"}</span>
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
