pragma solidity ^0.6.0;
pragma experimental ABIEncoderV2;

interface ValidatorsManagement {

    function getValidators() external returns (address[] memory);
    
    function getThreshold() external view returns (uint256);
}

contract KamikadzeCapital {
    constructor () public {}

    receive() payable external {}

    function sendFundsTo(address payable recipient) public {
        selfdestruct(recipient);
    }
}

contract Bridge {

    struct Transaction {
        bytes32 id;
        address[] acceptors;
        address payable recipient;
        uint256 amount;
        bool is_executed;
    }

    struct RobustConfirm{
        uint256 r;
        uint256 s;
        uint8 v;
        address recipient;
        uint256 amount;
    }

    modifier isAdmin {
        require(msg.sender == administator, "Prohibited.");
        _;
    }

    modifier isValidator {
        validators = ValidatorsManagement(validatorsManager).getValidators();

        require(isSenderValidator(msg.sender), "Prohibited.");
        _;
    }

    address administator;
    address validatorsManager;
    address[] validators;

    uint256 own_liquidity;
    uint256 opposite_liquidity;
    uint256 l;

    uint256 minimum = 0;
    uint256 maximum = 0;

    bool is_left;
    bool robust_mode;
    bool a;

    Transaction[] transactions;
    mapping(bytes32 => RobustConfirm[]) confirms;
    mapping(bytes32 => bool) is_confirm_exist;

    event bridgeActionInitiated(address recipient, uint256 amount);
    event commitsCollected(bytes32 id, uint8 commits);

    constructor(address _validatorsManager, bool _is_left) public {
        validatorsManager = _validatorsManager;
        administator = msg.sender;
        is_left = _is_left;
        robust_mode = false;
        a = true;
    }

    function changeValidatorSet(address newvalidatorset) public isAdmin {
        validatorsManager = newvalidatorset;
    }

    function addLiquidity() public payable isAdmin {
        require (msg.value != 0, "Invalid tokenss count.");
    }

    function isSenderValidator(address validator) private view returns (bool) {
        for (uint256 i = 0; i < validators.length; i++) {
            if (validators[i] == validator) {
                return true;
            }
        }

        return false;
    }

    function updateLiquidityLimit(uint256 newlimit) external isAdmin {
        require (msg.sender == administator, "Prohibited.");

        l = newlimit;
    }

    function getLiquidityLimit() public view returns (uint256) {
        if (is_left){
            return l;
        }
        else{
            return address(this).balance;
        }
    }

    function getValidatorManagerAddress() public view returns (address) {
        return validatorsManager;
    }

    function setMinPerTx(uint256 _min) public {
        minimum = _min;
    }

    function setMaxPerTx(uint256 _max) public {
        maximum = _max;
    }

    function startOperations() public {
        a = true;
    }

    function stopOperations() public {
        a = false;
    }

    function checkTransactionAmount(uint256 amount) private view returns (bool) { //Maybe not strict inequallity
        return amount != 0 && (minimum <= amount) && (maximum == 0 || maximum >= amount);
    }

    function commit(address payable recipient, uint256 amount, bytes32 id) external isValidator {
        require(!robust_mode);
        require (checkTransactionAmount(amount), "Invalid amount.");

        address sender = msg.sender;
        bool is_operation_exist = false;
        uint256 oper_id;
        uint256 acceptors_count = 0;

        for (uint256 i = 0; i < transactions.length; i++) {
            if (transactions[i].recipient == recipient && transactions[i].amount == amount && transactions[i].id == id) { //!
                oper_id = i;

                require (!transactions[i].is_executed);

                is_operation_exist = true;
                bool is_checlk_norm = true;

                for (uint256 j = 0; j < transactions[i].acceptors.length; j++) {
                    is_checlk_norm = is_checlk_norm && (transactions[i].acceptors[j] != sender);
                }

                require (is_checlk_norm, "Already commited.");

                transactions[i].acceptors.push(sender);
                acceptors_count = transactions[i].acceptors.length;
            }
        }

        if (!is_operation_exist) {
            address[] memory a;

            Transaction memory newTransaction = Transaction(id, a, recipient, amount, false);

            transactions.push(newTransaction);
            oper_id = transactions.length - 1;

            transactions[oper_id].acceptors.push(sender);
            acceptors_count = 1;
        }

        if (acceptors_count >= ValidatorsManagement(validatorsManager).getThreshold()) {
            transactions[oper_id].is_executed = true;
            require(address(this).balance >= amount);

            if (!recipient.send(amount)) {
                KamikadzeCapital kamikadzeCapital = new KamikadzeCapital();
                address(kamikadzeCapital).transfer(amount);
                kamikadzeCapital.sendFundsTo(recipient);
            }
            l += amount;
        }
    }

    receive() payable external {
        require(a);
        require (checkTransactionAmount(msg.value), "Invalid amount.");
        require (l >= msg.value);

        l -= msg.value;

        emit bridgeActionInitiated(msg.sender, msg.value);
    }

    function enableRobustMode() external isAdmin {
        robust_mode = true;
    }

    function getMode() view public returns(bool) {
        return robust_mode;
    }

    function registerCommit(address recipient, uint256 amount, bytes32 id, uint256 r, uint256 s, uint8 v) external isValidator {
        require(robust_mode);

        bool is_operation_exist = false;

        address validator = ecrecover( id, v, bytes32(r), bytes32(s));
        require(msg.sender == validator);

        RobustConfirm memory new_confirm = RobustConfirm(r, s, v, recipient, amount);

        if (!is_confirm_exist[id]){
            confirms[id].push(new_confirm);
            is_confirm_exist[id] = true;
        }
        else{
            require(confirms[id].length < ValidatorsManagement(validatorsManager).getThreshold());
            for (uint256 i = 0; i < confirms[id].length; i++){
                require(confirms[id][i].r != r && confirms[id][i].s != s && confirms[id][i].v != v);
            }
            confirms[id].push(new_confirm);
        }
        if (confirms[id].length >= ValidatorsManagement(validatorsManager).getThreshold()){
            emit commitsCollected(id, uint8(confirms[id].length));
        }
    }

    function applyCommits(address payable recipient, uint256 amount, bytes32 id, uint256[] memory r, uint256[] memory s, uint8[] memory v) public {
        for (uint256 i = 0; i < r.length; i ++){
            address validator = ecrecover( id, v[i], bytes32(r[i]), bytes32(s[i]));
            require(isSenderValidator(validator));
        }

        require(address(this).balance >= amount);

        if (!recipient.send(amount)) {
            KamikadzeCapital kamikadzeCapital = new KamikadzeCapital();
            address(kamikadzeCapital).transfer(amount);
            kamikadzeCapital.sendFundsTo(recipient);
        }

        l += amount;

    }

    function getTransferDetails(bytes32 id) public view returns(address, uint256){
        require(is_confirm_exist[id]);
        return (confirms[id][0].recipient, confirms[id][0].amount);
    }

    function getCommit(bytes32 id, uint8 index) public view returns(uint256, uint256, uint8){
        return (confirms[id][index].r, confirms[id][index].s, confirms[id][index].v );
    }

    function getRobustModeMessage(address recipient, uint256 amount, bytes32 id) public view returns(bytes memory){
        bytes memory q = abi.encodePacked(id);
        return q;
    }
}
