/** Formats a number to add commas every three digits for easier viewing,
 *  e.g., 1000 -> 1,000
 *
 *  @param num Number to be formatted
 *  @return Formatted number (string)
 */
export const formattedNumber = (num) => num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
