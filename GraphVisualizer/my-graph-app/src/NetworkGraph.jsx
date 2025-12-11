  import React, { useEffect, useRef, useCallback } from 'react';
  import { DataSet, Network } from 'vis-network/standalone/esm/index';

  const NetworkGraph = ({ data, onNodeSelect, onEdgeSelect }) => {
    const containerRef = useRef(null);
    const networkRef = useRef(null);

    // Process the data to extract labels and types for visualization
    const processGraphData = useCallback((rawData) => {
      // Define the color palette from the README
      const colorPalette = [
        '#c33149ff', // $intense-cherry
        '#7b5c60ff', // $smoky-rose
        '#338776ff', // $jungle-teal
        '#46ac67ff', // $jungle-green
        '#a8c256ff', // $yellow-green
        '#cece84ff', // $golden-sand
        '#f3d9b1ff', // $wheat
        '#c29979ff', // $camel
        '#b25f4eff', // $terracotta-clay
        '#863936ff'  // $brown-red
      ];

      // Create a map to store which color index each entity type has been assigned
      const entityColorMap = new Map();

      // Function to get color from the predefined palette based on entity type
      const getColorFromType = (nodeType) => {
        // If we've already assigned a color to this entity type, use it
        if (entityColorMap.has(nodeType)) {
          const colorIndex = entityColorMap.get(nodeType);
          const baseColor = colorPalette[colorIndex];

          // Generate highlight color by lightening the base color
          const hexToHsl = (hex) => {
            // Remove # and parse hex values
            const cleanHex = hex.replace('#', '');
            const r = parseInt(cleanHex.substr(0, 2), 16) / 255;
            const g = parseInt(cleanHex.substr(2, 2), 16) / 255;
            const b = parseInt(cleanHex.substr(4, 2), 16) / 255;

            const max = Math.max(r, g, b);
            const min = Math.min(r, g, b);
            let h, s, l = (max + min) / 2;

            if (max === min) {
              h = s = 0; // achromatic
            } else {
              const d = max - min;
              s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
              switch (max) {
                case r: h = (g - b) / d + (g < b ? 6 : 0); break;
                case g: h = (b - r) / d + 2; break;
                case b: h = (r - g) / d + 4; break;
              }
              h /= 6;
            }

            return [Math.round(h * 360), Math.round(s * 100), Math.round(l * 100)];
          };

          const [h, s, l] = hexToHsl(baseColor);
          const highlightColor = `hsl(${h}, ${s}%, ${Math.min(100, l + 20)}%)`;

          return {
            background: baseColor,
            border: baseColor,
            highlight: {
              background: highlightColor,
              border: highlightColor
            },
            hover: {
              background: highlightColor,
              border: highlightColor
            }
          };
        }

        // Calculate a consistent index for the entity type to ensure consistent color assignment
        let hash = 0;
        for (let i = 0; i < nodeType.length; i++) {
          hash = nodeType.charCodeAt(i) + ((hash << 5) - hash);
        }

        // Use the hash to determine which color from the palette to use
        const colorIndex = Math.abs(hash) % colorPalette.length;
        entityColorMap.set(nodeType, colorIndex);

        const baseColor = colorPalette[colorIndex];

        // Generate highlight color by lightening the base color
        const hexToHsl = (hex) => {
          // Remove # and parse hex values
          const cleanHex = hex.replace('#', '');
          const r = parseInt(cleanHex.substr(0, 2), 16) / 255;
          const g = parseInt(cleanHex.substr(2, 2), 16) / 255;
          const b = parseInt(cleanHex.substr(4, 2), 16) / 255;

          const max = Math.max(r, g, b);
          const min = Math.min(r, g, b);
          let h, s, l = (max + min) / 2;

          if (max === min) {
            h = s = 0; // achromatic
          } else {
            const d = max - min;
            s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
            switch (max) {
              case r: h = (g - b) / d + (g < b ? 6 : 0); break;
              case g: h = (b - r) / d + 2; break;
              case b: h = (r - g) / d + 4; break;
            }
            h /= 6;
          }

          return [Math.round(h * 360), Math.round(s * 100), Math.round(l * 100)];
        };

        const [h, s, l] = hexToHsl(baseColor);
        const highlightColor = `hsl(${h}, ${s}%, ${Math.min(100, l + 10)}%)`;

        return {
          background: baseColor,
          border: baseColor,
          highlight: {
            background: highlightColor,
            border: highlightColor
          },
          hover: {
            background: highlightColor,
            border: highlightColor
          }
        };
      };

      const nodes = rawData.nodes.map(node => {
        // Use color assignment from the predefined palette based on entity type
        const nodeType = node.attributes?.label || node.labels?.[0] || 'Unknown';
        const colorConfig = getColorFromType(nodeType);

        // ALL entities will use circle shape with text inside
        // Differentiation will be through color and size instead of shape

        let size = 20; // default size

        // Function to shorten label if it doesn't fit in the circle
        const shortenLabel = (label, size) => {
          // Calculate an approximate max length based on the node size
          // This is a rough approximation - actual fitting depends on font metrics
          const maxLength = Math.floor(size * 1.5); // Approximate max characters that fit

          if (label.length > maxLength) {
            return label.substring(0, maxLength - 3) + '...';
          }
          return label;
        };

        const originalLabel = node.attributes?.name || node.properties?.name || 'Unknown';
        const displayLabel = shortenLabel(originalLabel, size);

        return {
          id: node.key || node.id,
          label: displayLabel,
          title: originalLabel, // Show full name in tooltip
          group: nodeType,
          color: colorConfig,
          shape: 'circle', // Use circle for ALL entity types
          size: size,
          font: {
            color: getColorFromType(nodeType).highlight.background, // text-color (restoring original)
            size: 14,
            face: 'arial',
            strokeWidth: 5, // Width of the stroke around the text
            strokeColor: '#2e2b2aff',
            align: 'center' // Align text in the center of the node
          },
          // Enable text wrapping by setting maximum width for the node
          widthConstraint: {
            maximum: 100 // Maximum width in pixels before text wraps
          },
          heightConstraint: {
            maximum: 60 // Maximum width in pixels
          },
          shapeProperties: {
            borderDashes: false,
            borderRadius: 5,
            interpolation: true,
            useImageSize: false,
            useBorderWithImage: false
          }
        };
      });

      const edges = rawData.edges.map(edge => ({
        id: edge.key || edge.id,
        from: edge.source,
        to: edge.target,
        label: edge.attributes?.label || edge.type || '',
        color: {
          color: '#b2a18c88', // primary-color
          highlight: getColorFromType(edge.source).background,
          hover: getColorFromType(edge.source).background
        },
        arrows: 'to',
        smooth: {
          enabled: true,
          type: 'curvedCW', // Force all to curve the same way so they stack
          roundness: Math.random() // Adjusts how wide the bundle of edges gets
          // roundness: Math.random()
        },
        font: {
          align: 'top',
          background: 'none',
          color: '#a9967fc0', // primary-color
          strokeWidth: 0,
          size: 10
        }
      }));

      return { nodes, edges };
    }, []);

    useEffect(() => {
      // Clean up existing network if it exists
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }

      if (!data || !data.nodes || !data.edges) {
        return;
      }

      // Process the data for vis-network
      const processedData = processGraphData(data);
      
      const nodesDataset = new DataSet(processedData.nodes);
      const edgesDataset = new DataSet(processedData.edges);

      const networkData = {
        nodes: nodesDataset,
        edges: edgesDataset
      };

      const options = {
        autoResize: true,
        height: '100%',
        width: '100%',
        layout: {
          improvedLayout: false,
          randomSeed: 1 
        },
        physics: {
          // enabled: false;
          stabilization: false,
          barnesHut: {
            gravitationalConstant: -80000,
            springConstant: 0.001,
            springLength: 60
          },

          // 3. Performance caps
          maxVelocity: 30,    // Lower cap so nodes don't fly off-screen instantly
          minVelocity: 5,  // Stop calculating physics sooner (higher = stops sooner)
          timestep: 0.5,      // Lower timestep = more accurate/stable, less jittery
          adaptiveTimestep: true // Helps browser maintain 60fps
        },
        nodes: {
          scaling: {
            min: 20, // Node will never be smaller than this (pixels)
            max: 50,
            label: {
              enabled: true, // Connects text size to node size
              min: 20,       // Text will never be smaller than 10px
              max: 50,
              maxVisible: 50 // Hides text completely if zoomed way too far out
            }
          }
        },
        edges: {
          scaling: {
            min: 5,
            max: 15
          },
          // smooth: {
          //   type: 'curvedCW',
          //   roundness: 0.2
          // }
        },
        interaction: {
          hover: true,
          selectConnectedEdges: true
        }
      };

      // Create the network
      networkRef.current = new Network(containerRef.current, networkData, options);

      // Event handlers for node and edge selection
      networkRef.current.on('click', function(params) {
        if (params.nodes.length > 0) {
          // Node was clicked
          const nodeId = params.nodes[0];
          const node = data.nodes.find(n => (n.key === nodeId) || (n.id === nodeId));
          if (node) {
            onNodeSelect(node);
          }
        } else if (params.edges.length > 0) {
          // Edge was clicked
          const edgeId = params.edges[0];
          const edge = data.edges.find(e => (e.key === edgeId) || (e.id === edgeId));
          if (edge) {
            onEdgeSelect(edge);
          }
        } else {
          // Clicked on empty space
          onNodeSelect(null);
        }
      });

      // Cleanup on unmount
      return () => {
        if (networkRef.current) {
          networkRef.current.destroy();
          networkRef.current = null;
        }
      };
    }, [data, processGraphData, onNodeSelect, onEdgeSelect]);

    return <div ref={containerRef} className="network-container" />;
  };

  export default NetworkGraph;