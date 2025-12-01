import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ChevronDown, ChevronUp } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { AppMode } from "@/pages/Index";
import { extractFormattedReport, truncateManagerReport } from "@/lib/markdown-utils";
import { FuturisticLoader } from "@/components/FuturisticLoader";

interface ResultsDisplayProps {
  mode: Exclude<AppMode, null>;
  isLoading: boolean;
  results: any;
}

export const ResultsDisplay = ({ mode, isLoading, results }: ResultsDisplayProps) => {
  const [isAnalystReportsOpen, setIsAnalystReportsOpen] = useState(false);
  const [isHumanRatingRevealed, setIsHumanRatingRevealed] = useState(false);
  const isExplainer = mode === "explainer";

  if (isLoading) {
    return (
      <Card className="p-12 text-center relative overflow-hidden border-2 border-primary/20 glass-chrome">
        <div className="relative">
          <FuturisticLoader 
            mode={mode}
            message={
              isExplainer 
                ? "Explainer Manager is collecting reports from the 3 analysts..." 
                : "Recommender Manager is aggregating analyst views..."
            }
          />
          <h3 className="text-2xl font-bold mt-8 bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
            Analyzing...
          </h3>
        </div>
      </Card>
    );
  }

  if (!results) return null;

  return (
    <div className="space-y-8">
      {/* Rating Comparison - Moved to top for recommender */}
      {!isExplainer && results.final_rating && (
        <Card className="p-8 glass-chrome border-2 border-recommender/40 relative overflow-hidden">
          <div className="relative">
            <h3 className="text-2xl font-bold mb-6 flex items-center gap-3">
              <span className="w-1 h-8 rounded-full bg-gradient-to-b from-recommender to-recommender/50" />
              Model Recommendation
            </h3>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="p-8 rounded-2xl glass-chrome border-2 border-recommender/40 shadow-lg relative overflow-hidden group hover:scale-[1.02] transition-transform duration-300 glow-silver">
                <div className="absolute top-0 right-0 w-32 h-32 rounded-full blur-2xl bg-recommender/30 group-hover:bg-recommender/40 transition-colors" />
                <div className="relative">
                  <p className="text-sm font-mono text-muted-foreground mb-3 uppercase tracking-wider">Model Rating (AI)</p>
                  <p className="text-5xl font-black text-recommender drop-shadow-lg">{results.final_rating}</p>
                  <div className="mt-4 flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-recommender animate-pulse" />
                    <span className="text-xs font-mono text-muted-foreground">AI Generated</span>
                  </div>
                </div>
              </div>
              <div 
                className="p-8 rounded-2xl glass-dark border-2 border-border/60 shadow-lg relative overflow-hidden group hover:scale-[1.02] transition-transform duration-300 cursor-pointer"
                onClick={() => setIsHumanRatingRevealed(!isHumanRatingRevealed)}
              >
                <div className="absolute top-0 right-0 w-32 h-32 rounded-full blur-2xl bg-muted/30 group-hover:bg-muted/40 transition-colors" />
                <div className="relative">
                  <p className="text-sm font-mono text-muted-foreground mb-3 uppercase tracking-wider">Human Analyst (IBES)</p>
                  <div className="relative">
                    <p 
                      className={`text-5xl font-black drop-shadow-lg transition-all duration-300 ${
                        isHumanRatingRevealed 
                          ? "text-foreground blur-0" 
                          : "text-foreground/20 blur-md"
                      }`}
                    >
                      {results.human_rating || "N/A"}
                    </p>
                    {!isHumanRatingRevealed && (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <p className="text-sm text-muted-foreground font-medium">Click to reveal</p>
                      </div>
                    )}
                  </div>
                  <div className="mt-4 flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-muted-foreground" />
                    <span className="text-xs font-mono text-muted-foreground">Reference</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}

      <Card className={`p-10 relative overflow-hidden border-2 glass-chrome ${
        isExplainer ? "border-explainer/40" : "border-recommender/40"
      }`}>
        <div className={`absolute top-0 right-0 w-64 h-64 rounded-full blur-3xl opacity-30 ${
          isExplainer ? "bg-explainer glow-chrome" : "bg-recommender glow-silver"
        }`} />
        <div className="relative">
          <div className="flex items-center gap-4 mb-8">
            <div className={`w-14 h-14 rounded-xl flex items-center justify-center text-2xl shadow-lg ${
              isExplainer 
                ? "bg-gradient-to-br from-explainer to-explainer/80 text-white" 
                : "bg-gradient-to-br from-recommender to-recommender/80 text-white"
            }`}>
              {isExplainer ? "🔍" : "🎯"}
            </div>
            <div>
              <h2 className="text-3xl font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                {isExplainer ? "Explainer Manager Report" : "Recommender Manager Report"}
              </h2>
              <p className="text-sm text-muted-foreground mt-1 font-mono">
                {new Date().toLocaleDateString()} • AI-Generated Analysis
              </p>
            </div>
          </div>
          
          <div className="prose prose-lg max-w-none dark:prose-invert 
            prose-headings:font-bold prose-headings:tracking-tight
            prose-p:text-foreground/90 prose-p:leading-relaxed prose-p:text-base
            prose-strong:text-foreground prose-strong:font-bold
            prose-ul:text-foreground prose-ol:text-foreground
            prose-li:text-foreground/90 prose-li:leading-relaxed
            prose-code:bg-gradient-to-br prose-code:from-muted prose-code:to-muted/80 prose-code:px-2 prose-code:py-1 prose-code:rounded-md prose-code:text-sm prose-code:font-mono prose-code:text-primary prose-code:border prose-code:border-border/50
            prose-pre:bg-gradient-to-br prose-pre:from-muted prose-pre:to-muted/80 prose-pre:border prose-pre:border-border/50 prose-pre:rounded-lg prose-pre:p-4 prose-pre:overflow-x-auto
            prose-hr:border-t-2 prose-hr:border-gradient-to-r prose-hr:from-transparent prose-hr:via-border prose-hr:to-transparent prose-hr:my-8
            prose-blockquote:border-l-4 prose-blockquote:border-primary prose-blockquote:pl-6 prose-blockquote:italic prose-blockquote:bg-muted/30 prose-blockquote:py-2 prose-blockquote:rounded-r-lg prose-blockquote:my-6
            prose-a:text-primary prose-a:font-medium prose-a:underline prose-a:underline-offset-2 hover:prose-a:text-primary/80">
            <ReactMarkdown
              components={{
                h1: ({node, ...props}) => (
                  <h1 className="text-4xl font-bold mt-10 mb-6 text-foreground border-b-2 border-border/50 pb-4 bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent" {...props} />
                ),
                h2: ({node, ...props}) => (
                  <h2 className={`text-2xl font-bold mt-8 mb-4 text-foreground flex items-center gap-3 ${
                    isExplainer ? "text-explainer" : "text-recommender"
                  }`} {...props}>
                    <span className="w-1 h-8 rounded-full bg-gradient-to-b from-primary to-primary/50" />
                    <span {...props} />
                  </h2>
                ),
                h3: ({node, ...props}) => (
                  <h3 className="text-xl font-bold mt-6 mb-3 text-foreground flex items-center gap-2">
                    <span className={`w-1.5 h-1.5 rounded-full ${
                      isExplainer ? "bg-explainer" : "bg-recommender"
                    }`} />
                    <span {...props} />
                  </h3>
                ),
                h4: ({node, ...props}) => (
                  <h4 className="text-lg font-semibold mt-5 mb-2 text-foreground/90" {...props} />
                ),
                p: ({node, ...props}) => (
                  <p className="mb-5 text-foreground/90 leading-relaxed text-base" {...props} />
                ),
                ul: ({node, ...props}) => (
                  <ul className="list-none mb-6 space-y-3 text-foreground/90" {...props}>
                    {props.children}
                  </ul>
                ),
                ol: ({node, ...props}) => (
                  <ol className="list-decimal list-outside mb-6 ml-6 space-y-3 text-foreground/90 marker:font-bold marker:text-primary" {...props} />
                ),
                li: ({node, ...props}) => (
                  <li className="flex items-start gap-3 leading-relaxed pl-2">
                    <span className={`mt-2 w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                      isExplainer ? "bg-explainer" : "bg-recommender"
                    }`} />
                    <span {...props} />
                  </li>
                ),
                strong: ({node, ...props}) => (
                  <strong className="font-bold text-foreground" {...props} />
                ),
                em: ({node, ...props}) => (
                  <em className="italic text-foreground/80" {...props} />
                ),
                code: ({node, inline, ...props}: any) => 
                  inline ? (
                    <code className="bg-gradient-to-br from-muted to-muted/80 px-2 py-1 rounded-md text-sm font-mono text-primary border border-border/50" {...props} />
                  ) : (
                    <code className="block bg-gradient-to-br from-muted to-muted/80 p-4 rounded-lg text-sm font-mono text-foreground border border-border/50 overflow-x-auto" {...props} />
                  ),
                hr: ({node, ...props}) => (
                  <hr className="my-8 border-0 h-px bg-gradient-to-r from-transparent via-border to-transparent" {...props} />
                ),
                blockquote: ({node, ...props}) => (
                  <blockquote className={`border-l-4 ${
                    isExplainer ? "border-explainer" : "border-recommender"
                  } pl-6 italic my-6 bg-muted/30 py-3 rounded-r-lg text-foreground/80`} {...props} />
                ),
              }}
            >
              {isExplainer 
                ? extractFormattedReport(results.manager_report || "")
                : truncateManagerReport(extractFormattedReport(results.manager_report || ""), 5)
              }
            </ReactMarkdown>
          </div>
        </div>
      </Card>

      <Collapsible open={isAnalystReportsOpen} onOpenChange={setIsAnalystReportsOpen}>
        <Card className="p-6 border-2 border-border/50 bg-gradient-to-br from-card to-card/50 relative overflow-hidden">
          <div className={`absolute inset-0 bg-gradient-to-r from-transparent ${
            isExplainer ? "via-explainer/5" : "via-recommender/5"
          } to-transparent opacity-0 transition-opacity duration-300 ${isAnalystReportsOpen ? "opacity-100" : ""} pointer-events-none`} />
          <CollapsibleTrigger asChild>
            <Button variant="ghost" className="w-full justify-between p-6 h-auto hover:bg-muted/50 transition-all duration-300 rounded-xl group">
              <span className="text-xl font-bold flex items-center gap-3">
                <span className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg ${
                  isExplainer 
                    ? "bg-explainer/10 text-explainer group-hover:bg-explainer/20" 
                    : "bg-recommender/10 text-recommender group-hover:bg-recommender/20"
                } transition-colors`}>
                  👥
                </span>
                <span className="bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                  View detailed work from the 3 analysts
                </span>
              </span>
              {isAnalystReportsOpen ? (
                <ChevronUp className="w-6 h-6 transition-transform duration-300" />
              ) : (
                <ChevronDown className="w-6 h-6 transition-transform duration-300" />
              )}
            </Button>
          </CollapsibleTrigger>
          
          <CollapsibleContent className="space-y-6 mt-6">
            {Object.entries(results.analyst_reports).map(([analyst, report], index) => {
              const analystColors = [
                { bg: "from-blue-500/10 to-blue-500/5", border: "border-blue-500/20", text: "text-blue-600", icon: "📊" },
                { bg: "from-purple-500/10 to-purple-500/5", border: "border-purple-500/20", text: "text-purple-600", icon: "📈" },
                { bg: "from-green-500/10 to-green-500/5", border: "border-green-500/20", text: "text-green-600", icon: "📰" },
              ];
              const colors = analystColors[index] || analystColors[0];
              
              return (
                <Card key={analyst} className={`p-8 bg-gradient-to-br ${colors.bg} border-2 ${colors.border} relative overflow-hidden group hover:scale-[1.01] transition-transform duration-300`}>
                  <div className={`absolute top-0 right-0 w-40 h-40 rounded-full blur-3xl opacity-10 ${
                    index === 0 ? "bg-blue-500" : index === 1 ? "bg-purple-500" : "bg-green-500"
                  } group-hover:opacity-20 transition-opacity`} />
                  <div className="relative">
                    <h3 className="text-xl font-bold mb-6 flex items-center gap-3">
                      <span className={`w-12 h-12 rounded-xl flex items-center justify-center text-2xl bg-gradient-to-br ${
                        index === 0 ? "from-blue-500 to-blue-600" : index === 1 ? "from-purple-500 to-purple-600" : "from-green-500 to-green-600"
                      } text-white shadow-lg`}>
                        {colors.icon}
                      </span>
                      <span>
                        <span className={`text-sm font-mono ${colors.text} block mb-1`}>Analyst #{index + 1}</span>
                        {analyst === "fundamental" && "Fundamental Analyst Report"}
                        {analyst === "technical" && "Technical Analyst Report"}
                        {analyst === "news" && "News & Sentiment Analyst Report"}
                      </span>
                    </h3>
                    <div className="prose prose-base max-w-none dark:prose-invert 
                      prose-headings:font-bold prose-headings:tracking-tight
                      prose-p:text-foreground/90 prose-p:leading-relaxed
                      prose-strong:text-foreground prose-strong:font-bold
                      prose-ul:text-foreground prose-ol:text-foreground
                      prose-li:text-foreground/90 prose-li:leading-relaxed
                      prose-code:bg-gradient-to-br prose-code:from-muted prose-code:to-muted/80 prose-code:px-2 prose-code:py-1 prose-code:rounded-md prose-code:text-sm prose-code:font-mono prose-code:text-primary prose-code:border prose-code:border-border/50
                      prose-hr:border-t-2 prose-hr:my-6
                      prose-blockquote:border-l-4 prose-blockquote:border-primary prose-blockquote:pl-6 prose-blockquote:italic prose-blockquote:bg-muted/30 prose-blockquote:py-2 prose-blockquote:rounded-r-lg">
                      <ReactMarkdown
                        components={{
                          h1: ({node, ...props}) => (
                            <h1 className="text-3xl font-bold mt-8 mb-5 text-foreground border-b-2 border-border/50 pb-3" {...props} />
                          ),
                          h2: ({node, ...props}) => (
                            <h2 className={`text-xl font-bold mt-6 mb-3 flex items-center gap-2 ${colors.text}`} {...props}>
                              <span className={`w-1 h-6 rounded-full ${
                                index === 0 ? "bg-blue-500" : index === 1 ? "bg-purple-500" : "bg-green-500"
                              }`} />
                              <span {...props} />
                            </h2>
                          ),
                          h3: ({node, ...props}) => (
                            <h3 className="text-lg font-bold mt-5 mb-2 text-foreground" {...props} />
                          ),
                          p: ({node, ...props}) => (
                            <p className="mb-4 text-foreground/90 leading-relaxed" {...props} />
                          ),
                          ul: ({node, ...props}) => (
                            <ul className="list-none mb-5 space-y-2.5" {...props}>
                              {props.children}
                            </ul>
                          ),
                          ol: ({node, ...props}) => (
                            <ol className="list-decimal list-outside mb-5 ml-6 space-y-2.5 marker:font-bold" {...props} />
                          ),
                          li: ({node, ...props}) => (
                            <li className="flex items-start gap-3 leading-relaxed pl-2">
                              <span className={`mt-2 w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                                index === 0 ? "bg-blue-500" : index === 1 ? "bg-purple-500" : "bg-green-500"
                              }`} />
                              <span {...props} />
                            </li>
                          ),
                          strong: ({node, ...props}) => (
                            <strong className="font-bold text-foreground" {...props} />
                          ),
                          em: ({node, ...props}) => (
                            <em className="italic text-foreground/80" {...props} />
                          ),
                          code: ({node, inline, ...props}: any) => 
                            inline ? (
                              <code className="bg-gradient-to-br from-muted to-muted/80 px-2 py-1 rounded-md text-sm font-mono text-primary border border-border/50" {...props} />
                            ) : (
                              <code className="block bg-gradient-to-br from-muted to-muted/80 p-4 rounded-lg text-sm font-mono text-foreground border border-border/50 overflow-x-auto" {...props} />
                            ),
                          hr: ({node, ...props}) => (
                            <hr className="my-6 border-0 h-px bg-gradient-to-r from-transparent via-border to-transparent" {...props} />
                          ),
                          blockquote: ({node, ...props}) => (
                            <blockquote className={`border-l-4 ${
                              index === 0 ? "border-blue-500" : index === 1 ? "border-purple-500" : "border-green-500"
                            } pl-6 italic my-5 bg-muted/30 py-2 rounded-r-lg text-foreground/80`} {...props} />
                          ),
                        }}
                      >
                        {extractFormattedReport((report as string) || "")}
                      </ReactMarkdown>
                    </div>
                  </div>
                </Card>
              );
            })}
          </CollapsibleContent>
        </Card>
      </Collapsible>
    </div>
  );
};
