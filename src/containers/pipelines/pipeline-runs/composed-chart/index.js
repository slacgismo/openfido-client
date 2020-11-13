import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import moment from 'moment';
import {
  ResponsiveContainer,
  ComposedChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Area,
  Bar,
  Label,
  Tooltip,
} from 'recharts';

import { requestArtifact } from 'services';
import {
  chartTypes, chartFills, chartStrokes, XAXIS, YAXIS,
} from 'config/charts';
import { parseCsvData } from 'util/charts';
import colors from 'styles/colors';
import CustomXAxisTick from './custom-x-axis-tick';
import CustomYAxisTick from './custom-y-axis-tick';

const TimeSeriesChart = ({
  type, config, height, artifact, sendChartData,
}) => {
  const axesComponents = [];
  const dataComponents = [];

  const [computedChartData, setComputedChartData] = useState(null);
  const [computedChartTypes, setComputedChartTypes] = useState({});
  const [computedChartScales, setComputedChartScales] = useState({});

  const axesFormatter = (value) => {
    if (value.toString().length === 10) {
      const dataValue = moment.unix(value);
      if (dataValue.isValid()) {
        return moment.unix(value).format('M/D/YYYY h:mm:ss A');
      }
    }

    return value;
  };

  useEffect(() => {
    if (!computedChartData) {
      const useChartData = (data, types, scales) => {
        setComputedChartData(data);
        setComputedChartTypes(types);
        setComputedChartScales(scales);

        if (sendChartData) sendChartData(data);
      };

      requestArtifact(artifact)
        .then((response) => {
          parseCsvData(response.data, useChartData);
        });
    }
  }, [computedChartData, artifact, sendChartData]);

  if (config && config[XAXIS] && config[YAXIS] && chartFills && chartStrokes) {
    const allNumberYAxes = [];

    config[YAXIS].forEach((axis, index) => {
      const isNumberType = computedChartTypes[axis] === 'number';

      if (axis in computedChartTypes && axis in computedChartScales) {
        switch (computedChartTypes[axis]) {
          case 'number':
            allNumberYAxes.push(axis);
            break;
          case 'time':
            axesComponents.push((
              <YAxis
                key={`yAxis${axis}`}
                yAxisId={`${axis}${index}`}
                scale={computedChartScales[axis] || 'time'}
                type="number"
                interval="preserveStartEnd"
                domain={['auto', 'auto']}
                fontSize={12}
                style={{ fontWeight: '500', fill: colors.gray10 }}
                tickLine={false}
                tickSize={0}
                tickCount={5}
                tick={<CustomYAxisTick isTimestamp />}
              />
            ));
            break;
          case 'category':
          default:
            axesComponents.push((
              <YAxis
                key={`yAxis${axis}`}
                yAxisId={`${axis}${index}`}
                type="category"
                domain={['high', 'low']}
                interval="preserveStartEnd"
                fontSize={12}
                style={{ fontWeight: '500', fill: colors.gray10 }}
                angle={-90}
                tickLine={false}
                tickSize={0}
                tickCount={5}
                tick={CustomYAxisTick}
                stroke={colors.gray10}
              >
                <Label
                  angle={-90}
                  value={axis}
                  position="insideLeft"
                  offset={-16}
                  style={{
                    textAnchor: 'middle', fontSize: 14, fontWeight: 'bold', fill: colors.gray,
                  }}
                />
              </YAxis>
            ));
            break;
        }
      }

      const yAxisId = isNumberType ? 'number' : `${axis}${index}`;

      switch (type) {
        case chartTypes.LINE_CHART: // TODO: toggle Area
          dataComponents.push((
            <Area
              key={`area${axis}`}
              dataKey={axis}
              yAxisId={yAxisId}
              dot={false}
              fill={chartFills[index]}
              stroke={chartStrokes[index]}
            />
          ));
          break;
        case chartTypes.BAR_CHART: // TODO: bar column legend
          dataComponents.push((
            <Bar
              key={`bar${axis}`}
              dataKey={axis}
              yAxisId={yAxisId}
              dot={false}
              fill={chartFills[index]}
              stroke={chartStrokes[index]}
            />
          ));
          break;
        default:
          break;
      }
    });

    if (allNumberYAxes.length) {
      axesComponents.push((
        <YAxis
          key="yAxisNumber"
          type="number"
          scale={computedChartScales[allNumberYAxes[0]] || 'auto'}
          interval="preserveStartEnd"
          yAxisId="number"
          fontSize={12}
          style={{ fontWeight: '500', fill: colors.gray10 }}
          angle={-90}
          tickLine={false}
          tickSize={0}
          tickCount={5}
          tick={CustomYAxisTick}
          stroke={colors.gray10}
        >
          <Label
            angle={-90}
            value={allNumberYAxes.join(', ')}
            position="insideLeft"
            offset={-16}
            style={{
              textAnchor: 'middle', fontSize: 14, fontWeight: 'bold', fill: colors.gray,
            }}
          />
        </YAxis>
      ));
    }

    config[XAXIS].forEach((axis) => {
      if (axis in computedChartTypes && axis in computedChartScales) {
        switch (computedChartTypes[axis]) {
          case 'time':
            axesComponents.push((
              <XAxis
                key={`xAxis${axis}`}
                dataKey={axis}
                type="number"
                scale="time"
                interval="preserveStartEnd"
                domain={['auto', 'auto']}
                fontSize={10}
                style={{ fontWeight: '500', fill: colors.gray10 }}
                tickLine={false}
                tickSize={0}
                tick={<CustomXAxisTick isTimestamp />}
              />
            ));
            break;
          case 'number':
            axesComponents.push((
              <XAxis
                key={`xAxis${axis}`}
                dataKey={axis}
                type="number"
                interval="preserveStartEnd"
                domain={['auto', 'auto']}
                fontSize={10}
                style={{ fontWeight: '500', fill: colors.gray10 }}
                tickLine={false}
                tickSize={0}
                stroke={colors.gray10}
                tick={CustomXAxisTick}
              />
            ));
            break;
          case 'category':
          default:
            axesComponents.push((
              <XAxis
                key={`xAxis${axis}`}
                dataKey={axis}
                interval="preserveStartEnd"
                fontSize={10}
                style={{ fontWeight: '500', fill: colors.gray10 }}
                tickLine={false}
                tickSize={0}
                stroke={colors.gray10}
                tick={CustomXAxisTick}
              />
            ));
            break;
        }
      }
    });
  }

  return (
    <ResponsiveContainer
      width="100%"
      height={height}
    >
      <ComposedChart
        height={height}
        data={computedChartData}
        margin={{
          bottom: 16,
          left: 32,
          right: 32,
        }}
      >
        <CartesianGrid stroke="rgba(112, 112, 112, 0.2)" vertical={false} />
        {axesComponents}
        {dataComponents}
        <Tooltip
          labelFormatter={axesFormatter}
          formatter={axesFormatter}
          contentStyle={{
            fontSize: 12,
            fontWeight: 400,
            lineHeight: '14px',
          }}
          labelStyle={{
            fontSize: 12,
            fontWeight: 'bold',
            lineHeight: '20px',
            color: colors.gray,
          }}
          cursor={{ stroke: colors.gray, strokeWidth: 1, strokeDasharray: '3, 3' }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
};

TimeSeriesChart.propTypes = {
  type: PropTypes.string.isRequired,
  config: PropTypes.shape({
    [XAXIS]: PropTypes.arrayOf(PropTypes.string).isRequired,
    [YAXIS]: PropTypes.arrayOf(PropTypes.string).isRequired,
  }).isRequired,
  artifact: PropTypes.shape({
    name: PropTypes.string.isRequired,
    url: PropTypes.string.isRequired,
    uuid: PropTypes.string.isRequired,
  }).isRequired,
  height: PropTypes.number,
  sendChartData: PropTypes.func,
};

TimeSeriesChart.defaultProps = {
  height: 264,
  sendChartData: null,
};

export default TimeSeriesChart;
