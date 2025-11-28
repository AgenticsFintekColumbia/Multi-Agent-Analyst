import { Card } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";

interface TimeWindowControlsProps {
  fundWindow: number;
  newsWindow: number;
  onFundWindowChange: (value: number) => void;
  onNewsWindowChange: (value: number) => void;
}

export const TimeWindowControls = ({
  fundWindow,
  newsWindow,
  onFundWindowChange,
  onNewsWindowChange,
}: TimeWindowControlsProps) => {
  return (
    <Card className="p-6 space-y-6">
      <h3 className="text-lg font-semibold">Time Windows</h3>

      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="text-sm font-medium">FUND Window</label>
          <span className="text-sm font-semibold text-primary">{fundWindow} days</span>
        </div>
        <Slider
          value={[fundWindow]}
          onValueChange={([value]) => onFundWindowChange(value)}
          min={7}
          max={90}
          step={1}
          className="w-full"
        />
        <p className="text-xs text-muted-foreground mt-2">
          Historical fundamental data lookback period
        </p>
      </div>

      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="text-sm font-medium">NEWS Window</label>
          <span className="text-sm font-semibold text-success">{newsWindow} days</span>
        </div>
        <Slider
          value={[newsWindow]}
          onValueChange={([value]) => onNewsWindowChange(value)}
          min={1}
          max={30}
          step={1}
          className="w-full"
        />
        <p className="text-xs text-muted-foreground mt-2">
          News and sentiment analysis lookback period
        </p>
      </div>
    </Card>
  );
};
