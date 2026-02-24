export class TatorLocalizationType {
    static BOX = 48;
    static DOT = 49;
    static SUB_BOX = 794;
    static SUB_DOT = 795;

    static isBox(localizationType) {
        return localizationType === this.BOX || localizationType === this.SUB_BOX;
    }

    static isDot(localizationType) {
        return localizationType === this.DOT || localizationType === this.SUB_DOT;
    }
}
