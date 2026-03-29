export function downloadTsv(headers, rows, title) {
    let tsvContent = 'data:text/tsv;charset=utf-8,';
    tsvContent += headers.join('\t') + '\n';
    rows.forEach((rowArray) => {
        const row = rowArray.join('\t');
        tsvContent += row + '\n';
    });
    const encodedUri = encodeURI(tsvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${title}.tsv`);
    document.body.appendChild(link);
    link.click();
}
