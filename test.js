
/*const buildings = {
    'Cottage': {'1, 1': 'blue', '0, 1': 'red', '1, 0': 'yellow'},
    'Fountain': {'0, 0': 'brown', '0, 1': 'gray'},
    'Millstone': {'0, 0': 'brown', '0, 1': 'gray'},
    'Shed': {'0, 0': 'brown', '0, 1': 'gray'},
    'Well': {'0, 0': 'brown', '0, 1': 'gray'},
    'Feast hall': {'0, 0': 'brown', '0, 1': 'brown', '0, 2': 'blue'},
    'Tavern': {'0, 0': 'red', '0, 1': 'red', '0, 2': 'blue'},
    'Inn': {'0, 0': 'yellow', '0, 1': 'gray', '0, 2': 'blue'},
    'Almshouse': {'0, 0': 'gray', '0, 1': 'gray', '0, 2': 'blue'},
    'Temple': {'0, 2': 'red', '0, 1': 'red', '0, 0': 'gray', '1, 0': 'blue'},
    'Abbey': {'0, 2': 'red', '0, 1': 'gray', '0, 0': 'gray', '1, 0': 'blue'},
    'Chapel': {'0, 2': 'gray', '0, 1': 'blue', '0, 0': 'gray', '1, 0': 'blue'},
    'Cloister': {'0, 2': 'brown', '0, 1': 'red', '0, 0': 'gray', '1, 0': 'blue'},
    'Orchard': {'0, 0': 'yellow', '1, 1': 'yellow', '1, 0': 'brown', '0, 1': 'gray'},
    'Farm': {'0, 0': 'brown', '1, 1': 'yellow', '1, 0': 'brown', '0, 1': 'yellow'},
    'Granary': {'0, 0': 'brown', '1, 1': 'yellow', '1, 0': 'red', '0, 1': 'yellow'},
    'Greenhouse': {'0, 0': 'brown', '1, 1': 'yellow', '1, 0': 'brown', '0, 1': 'blue'},
    'Warehouse': {'0, 0': 'red', '0, 2': 'red', '1, 0': 'yellow', '1, 2': 'yellow', '1, 1': 'brown'}, 
    'Factory': {'0, 0': 'red', '0, 3': 'red', '1, 0': 'brown', '0, 2': 'gray', '0, 1': 'gray'},
    'Trading post': {'0, 0': 'gray', '0, 2': 'red', '1, 0': 'gray', '0, 1': 'brown', '1, 1': 'brown'},
    'Bank': {'0, 0': 'brown', '0, 2': 'red', '1, 0': 'yellow', '1, 1': 'yellow', '0, 1': 'blue'},
    'Theatre': {'0, 0': 'brown', '0, 1': 'blue', '0, 2': 'brown', '1, 1': 'gray'},
    'Bakery': {'0, 0': 'red', '0, 1': 'blue', '0, 2': 'red', '1, 1': 'yellow'},
    'Tailor': {'0, 0': 'gray', '0, 1': 'blue', '0, 2': 'gray', '1, 1': 'yellow'},
    'Market': {'0, 0': 'gray', '0, 1': 'blue', '0, 2': 'gray', '1, 1': 'brown'}
}

//const colors =  ['empty','blue','red','yellow'];
//const pattern = {'0, 1': 'yellow', '3, 1': 'red', '0, 0': 'brown', '1, 1': 'gray', '2, 1': 'gray'}  //
//const pattern = {'0, 0': 'red', '0, 3': 'red', '1, 0': 'brown', '0, 2': 'gray', '0, 1': 'gray'} //
//const pattern = {'1, 1': 'b', '0, 1': 'r', '1, 0': 'y'};



const getMatrix = (pattern) => {   
    const coords = Object.keys(pattern); 
    const width = Math.max(...coords.map(x => x.split(', ')[0])) + 1;
    const height = Math.max(...coords.map(x => x.split(', ')[1])) + 1;

    let matrix = [];
    for(var i=0; i<height; i++) {
        matrix[i] = [];
        for(var j=0; j<width; j++) {
            matrix[i][j] = '';
        }
    }

    for (let p in pattern) {
        const x = parseInt(p.split(', ')[0]);
        const y = parseInt(p.split(', ')[1]);

        matrix[y][x] = pattern[p];
    }
    
    return matrix;
};

*/

const showMatrix = (m) => {
    //return console.log(m)
    
    for (let line of m) {
        let row = ''
        for (let l of line) {
            row += (l ? l : ' ')+'\t'
        }
        console.log(row);     
    }
};




const buildings = {
    'Cottage':[['', 'yellow'],['red', 'blue']],
    'Fountain':[['brown'],['gray']],
    'Millstone':[['brown'],['gray']],
    'Shed':[['brown'],['gray']],
    'Well':[['brown'],['gray']],
    'Feast hall':[['brown'],['brown'],['blue']],
    'Tavern':[['red'],['red'],['blue']],
    'Inn':[['yellow'],['gray'],['blue']],
    'Almshouse':[['gray'],['gray'],['blue']],
    'Temple':[['gray', 'blue'],['red', ''],['red', '']],
    'Abbey':[['gray', 'blue'],['gray', ''],['red', '']],
    'Chapel':[['gray', 'blue'],['blue', ''],['gray', '']],
    'Cloister':[['gray', 'blue'],['red', ''],['brown', '']],
    'Orchard':[['yellow', 'brown'],['gray', 'yellow']],
    'Farm':[['brown', 'brown'],['yellow', 'yellow']],
    'Granary':[['brown', 'red'],['yellow', 'yellow']],
    'Greenhouse':[['brown', 'brown'],['blue', 'yellow']],
    'Warehouse':[['red', 'yellow'],['', 'brown'],['red', 'yellow']],
    'Factory':[['red', 'brown'],['gray', ''],['gray', ''],['red', '']],
    'Trading post':[['gray', 'gray'],['brown', 'brown'],['red', '']],
    'Bank':[['brown', 'yellow'],['blue', 'yellow'],['red', '']],
    'Theatre':[['brown', ''],['blue', 'gray'],['brown', '']],
    'Bakery':[['red', ''],['blue', 'yellow'],['red', '']],
    'Tailor':[['gray', ''],['blue', 'yellow'],['gray', '']],
    'Market':[['gray', ''],['blue', 'brown'],['gray', ''] ] 
}


const rotate = (matrix, count = 1) => {
    for (let i=0; i<count; i++) {
        matrix = matrix[0].map((val, index) => matrix.map(row => row[index]).reverse())
    }
    return matrix;
}
     
const transpose = (matrix) => {
    let [row] = matrix;
    return row.map((value, column) => matrix.map(row => row[column]))
}

const mirrorV = (matrix) => rotate(transpose(matrix))
const mirrorH = (matrix) => mirrorV(rotate(mirrorV(transpose((matrix)))));

let all = []
const m = buildings['Factory'];
for (let i=0;i<4;i++) {
    all.push(rotate(m, i));
    all.push(rotate(mirrorH(m),i))
    all.push(rotate(mirrorV(m),i))
    all.push(rotate(mirrorH(mirrorV(m)),i))    
}
//console.log(all.length)

// for (let a of all) {
//     showMatrix(a);  console.log()
// }

//console.log(all[0], all[0].length, all[0][0].length)
console.log(all.length)
// for (let bn in buildings) {
//     const m = getMatrix(buildings[bn]);
//     console.log(`'${bn}':`, m, ',')
// }