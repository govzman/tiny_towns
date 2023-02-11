import {buildingsPatterns} from './dict.js';

export const getPatterns = (buildingName) => {
    const rotate = (matrix, count = 1) => {
        for (let i = 0; i < count; i++) {
            matrix = matrix[0].map((val, index) => matrix.map((row) => row[index]).reverse());
        }
        return matrix;
    };

    const transpose = (matrix) => {
        const [row] = matrix;
        return row.map((value, column) => matrix.map((row) => row[column]));
    };

    const mirrorV = (matrix) => rotate(transpose(matrix));
    const mirrorH = (matrix) => mirrorV(rotate(mirrorV(transpose((matrix)))));

    const patterns = [];
    const m = buildingsPatterns[buildingName];

    for (let i = 0;i < 4;i++) {
        patterns.push(rotate(m, i));
        patterns.push(rotate(mirrorH(m), i));
        patterns.push(rotate(mirrorV(m), i));
        patterns.push(rotate(mirrorH(mirrorV(m)), i));
    }
    return patterns;
};
