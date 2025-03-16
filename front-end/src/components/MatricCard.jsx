import React from "react";
import Slider from "@mui/material/Slider";
import styles from "./MatricCard.module.scss";
import Box from "@mui/material/Box";

const MatricCard = ({
  marks = [0, 0, 0],
  matricName = "",
  formatMark = (txt) => txt,
}) => {
  const calculateDisplayRange = (marks) => {
    const [value, min, max] = marks;
    
    const actualMin = Math.min(value, min);
    const actualMax = Math.max(value, max);
    
    const range = actualMax - actualMin;
    const buffer = range * 0.1;
    const displayMin = actualMin - buffer;
    const displayMax = actualMax + buffer;
    const displayRange = displayMax - displayMin;
    
    return { displayMin, displayRange };
  };
  
  const calculateRelativePosition = (value, displayMin, displayRange) => {
    return ((value - displayMin) / displayRange) * 100;
  };

  const formatMarks = () => {
    const [value, min, max] = marks;
    const { displayMin, displayRange } = calculateDisplayRange(marks);

    const minPos = calculateRelativePosition(min, displayMin, displayRange);
    const valuePos = calculateRelativePosition(value, displayMin, displayRange);
    const maxPos = calculateRelativePosition(max, displayMin, displayRange);

    return [
      {
        value: minPos,
        label: formatMark(min) + ' (min)',
      },
      {
        value: valuePos,
        label: formatMark(value),
      },
      {
        value: maxPos,
        label: formatMark(max) + ' (max)',
      },
    ];
  };

  const getDefaultValue = () => {
    const [value] = marks;
    const { displayMin, displayRange } = calculateDisplayRange(marks);
    return calculateRelativePosition(value, displayMin, displayRange);
  };
  
  const getThumbColor = () => {
    // offset of medium range
    const MEDIUM_OFFSET = 0.2;
    const [value, min, max] = marks;
    
    // danger range
    if (value < min || value > max) {
      return '#e53935';
    }
    
    const range = max - min;
    const threshold = range * MEDIUM_OFFSET;
    
    // medium range
    if (value - min < threshold || max - value < threshold) {
      return '#f9a825';
    }
    // normal range
    return '#2e7d32';
  };

  const thumbColor = getThumbColor();

  return (
    <div className={styles.matricBox}>
      <div className={styles.info}>
        <span className={styles.name}>{matricName}</span>
      </div>
      <Box sx={{ width: 300 }}>
      <Slider
          aria-label="Custom marks"
          defaultValue={getDefaultValue()}
          getAriaValueText={formatMark}
          step={1}
          min={0}
          max={100}
          disabled={true}
          valueLabelDisplay="auto"
          marks={formatMarks()}
          sx={{
            color: 'rgba(0,0,0,0.87)',
            height: 4,
            '& .MuiSlider-thumb': {
              width: 16,
              height: 16,
              backgroundColor: thumbColor,
              '&::before': {
                boxShadow: '0 2px 12px 0 rgba(0,0,0,0.2)',
              },
            },
            '& .MuiSlider-track': {
                backgroundColor: thumbColor,
            },
            '& .MuiSlider-rail': {
              opacity: 0.5,
              backgroundColor: thumbColor,
            },
            '& .MuiSlider-markLabel': {
              fontSize: '0.75rem',
              fontWeight: 500,
            },
            // set value label color and bold
            '& .MuiSlider-markLabel[data-index="1"]': {
              color: thumbColor,
              fontWeight: 700,
            }
          }}
        />
      </Box>
    </div>
  );
};

export default MatricCard;