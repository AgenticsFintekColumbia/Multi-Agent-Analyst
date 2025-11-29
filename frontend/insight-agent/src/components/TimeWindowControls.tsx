import { Card } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { AppMode } from "@/pages/Index";

interface TimeWindowControlsProps {
  mode: Exclude<AppMode, null>;
  newsWindow: number;
  onNewsWindowChange: (value: number) => void;
  fundWindowDays?: number;
  technicalWindowDays?: number;
}

export const TimeWindowControls = ({
  mode,
  newsWindow,
  onNewsWindowChange,
  fundWindowDays = 90,
  technicalWindowDays = 90,
}: TimeWindowControlsProps) => {
  const isExplainer = mode === "explainer";

  return (
    <Card className="p-6 space-y-6 border border-border/50 bg-card/80 backdrop-blur-sm">
      <h3 className="text-lg font-semibold tracking-tight text-foreground">Time Windows</h3>

      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="text-sm font-semibold text-foreground">NEWS Window</label>
          <span className="text-sm font-bold text-success bg-success/10 px-2.5 py-1 rounded-md">{newsWindow} days</span>
        </div>
        <Slider
          value={[newsWindow]}
          onValueChange={([value]) => onNewsWindowChange(value)}
          min={30}
          max={60}
          step={1}
          accentColor="success"
          className="w-full"
        />
        <p className="text-xs text-muted-foreground mt-2.5 leading-relaxed">
          News and sentiment lookback period.
        </p>
      </div>

      <div className="pt-4 border-t border-border/30">
        <p className="text-xs text-muted-foreground leading-relaxed">
          {isExplainer ? (
            <>
              Fundamental lookback is fixed at <span className="font-semibold text-foreground">{fundWindowDays} days</span> and technical lookback is fixed at <span className="font-semibold text-foreground">{technicalWindowDays} days</span>.
            </>
          ) : (
            <>
              Fundamental and technical data use the latest available row before the recommendation date.
            </>
          )}
        </p>
      </div>
    </Card>
  );
};
